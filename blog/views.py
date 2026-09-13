from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.db.models import F, Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from .models import Post, Comment, Reaction, Profile, Follow, PostRead
from .forms import PostForm, CommentForm, ProfileForm
from django.urls import reverse
from django.utils import timezone
from django.template.defaultfilters import truncatewords
from datetime import date


def _absolute_media_url(request, url):
    """Cloudinary URLs are already absolute (https://...); local dev
    media URLs are relative and need the current host prepended. Only
    the latter should go through build_absolute_uri, or an already-
    absolute URL would get corrupted."""
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return request.build_absolute_uri(url)

LATEST_INITIAL = 5
POPULAR_INITIAL = 3
UNREAD_INITIAL = 5
LOAD_MORE_PAGE_SIZE = 5
COMMENTS_PER_PAGE = 5
SEARCH_RESULTS_PER_PAGE = 8
PROFILE_POSTS_PER_PAGE = 8
FOLLOWERS_PREVIEW_COUNT = 20
LIKERS_PREVIEW_COUNT = 30
USER_SEARCH_LIMIT = 10


def _ordered_published(post_type, request=None):
    published = Post.objects.filter(
        published_date__lte=timezone.now(), is_removed=False).select_related('author')
    if post_type == 'popular':
        return published.order_by('-view_count', '-published_date')
    if post_type == 'unread' and request is not None and request.user.is_authenticated:
        followed_ids = Follow.objects.filter(
            follower=request.user).values_list('following_id', flat=True)
        read_ids = PostRead.objects.filter(
            user=request.user).values_list('post_id', flat=True)
        return published.filter(author_id__in=followed_ids) \
            .exclude(pk__in=read_ids) \
            .order_by('-published_date')
    return published.order_by('-published_date')


def post_list(request):
    latest_qs = _ordered_published('latest')
    popular_qs = _ordered_published('popular')

    latest_posts = list(latest_qs[:LATEST_INITIAL])
    popular_posts = list(popular_qs[:POPULAR_INITIAL])

    context = {
        'latest_posts': latest_posts,
        'popular_posts': popular_posts,
        'has_more_latest': latest_qs.count() > len(latest_posts),
        'has_more_popular': popular_qs.count() > len(popular_posts),
    }

    if request.user.is_authenticated:
        unread_qs = _ordered_published('unread', request=request)
        unread_posts = list(unread_qs[:UNREAD_INITIAL])
        context['unread_posts'] = unread_posts
        context['has_more_unread'] = unread_qs.count() > len(unread_posts)

    return render(request, 'blog/post_list.html', context)


def post_more(request):
    post_type = request.GET.get('type')
    if post_type not in ('latest', 'popular', 'unread'):
        post_type = 'latest'
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
    except (TypeError, ValueError):
        offset = 0

    qs = _ordered_published(post_type, request=request)
    batch = list(qs[offset:offset + LOAD_MORE_PAGE_SIZE])
    html = render_to_string(
        'blog/_post_entries_batch.html', {'posts': batch}, request=request)

    return JsonResponse({
        'html': html,
        'count': len(batch),
        'has_more': offset + len(batch) < qs.count(),
    })


@login_required
def post_draft_list(request):
    posts = Post.objects.filter(
        published_date__isnull=True, author=request.user).order_by('created_date')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if post.published_date is None and post.author != request.user:
        raise Http404("Post not found")

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user

            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent = Comment.objects.filter(
                    pk=parent_id, post=post).first()
                if parent:
                    # Flatten replies-to-replies: always attach to the
                    # original top-level comment, so threads stay one
                    # level deep even if someone bypasses the UI.
                    comment.parent = parent.parent or parent

            comment.save()

            # Send the commenter to the page their new comment landed on.
            top_level_count = post.comments.filter(
                parent__isnull=True).count()
            last_page = max(
                1, -(-top_level_count // COMMENTS_PER_PAGE))  # ceil div
            url = reverse('post_detail', kwargs={'slug': post.slug})
            return redirect(f"{url}?page={last_page}#comments")
    else:
        form = CommentForm()
        Post.objects.filter(pk=post.pk).update(view_count=F('view_count') + 1)
        post.refresh_from_db()
        if request.user.is_authenticated:
            PostRead.objects.get_or_create(user=request.user, post=post)

    # Guests get a teaser (title + snippet + sign-up prompt), matching
    # the same pattern already used on the homepage feed — no comments,
    # reactions, or full text until they have an account. This also
    # means anonymous crawlers (link-preview bots for WhatsApp,
    # Telegram, etc.) can actually reach this page and read its real
    # meta tags, instead of being redirected to the login page first.
    if not request.user.is_authenticated:
        return render(request, 'blog/post_detail.html', {
            'post': post,
            'og_description': truncatewords(post.text, 30),
            'og_image_url': _absolute_media_url(request, post.image.url) if post.image else '',
        })

    top_level_qs = post.comments.filter(parent__isnull=True) \
        .select_related('author') \
        .prefetch_related('replies__author')
    paginator = Paginator(top_level_qs, COMMENTS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    comments_page = paginator.get_page(page_number)

    like_count = post.reactions.filter(value=Reaction.LIKE).count()
    dislike_count = post.reactions.filter(value=Reaction.DISLIKE).count()
    user_reaction = None
    if request.user.is_authenticated:
        existing = post.reactions.filter(user=request.user).first()
        user_reaction = existing.value if existing else None

    likers = None
    likers_total = 0
    if request.user == post.author:
        likers_qs = User.objects.filter(
            reaction__post=post, reaction__value=Reaction.LIKE
        ).select_related('profile')
        likers_total = likers_qs.count()
        likers = likers_qs[:LIKERS_PREVIEW_COUNT]

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments_page': comments_page,
        'total_comments': post.comments.count(),
        'comment_form': form,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'user_reaction': user_reaction,
        'likers': likers,
        'likers_total': likers_total,
        'og_description': truncatewords(post.text, 30),
        'og_image_url': _absolute_media_url(request, post.image.url) if post.image else '',
    })


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return redirect('post_detail', slug=post.slug)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return redirect('post_detail', slug=post.slug)
    post.publish()
    return redirect('post_detail', slug=post.slug)


@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        post.delete()
        return redirect('post_list')
    if request.user.is_staff:
        post.is_removed = True
        post.removed_by = request.user
        post.save()
        return redirect('post_detail', slug=post.slug)
    return redirect('post_detail', slug=post.slug)


@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author == request.user:
        comment.delete()
    elif request.user.is_staff:
        comment.is_removed = True
        comment.removed_by = request.user
        comment.save()
    return redirect('post_detail', slug=comment.post.slug)


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('post_list')
    else:
        form = UserCreationForm()
    return render(request, 'blog/signup.html', {'form': form})


@login_required
def post_react(request, pk, value):
    post = get_object_or_404(Post, pk=pk)
    if value not in (Reaction.LIKE, Reaction.DISLIKE):
        return redirect('post_detail', slug=post.slug)

    existing = Reaction.objects.filter(post=post, user=request.user).first()
    if existing and existing.value == value:
        existing.delete()
    elif existing:
        existing.value = value
        existing.save()
    else:
        Reaction.objects.create(post=post, user=request.user, value=value)

    like_count = post.reactions.filter(value=Reaction.LIKE).count()
    dislike_count = post.reactions.filter(value=Reaction.DISLIKE).count()
    user_reaction = post.reactions.filter(
        user=request.user).values_list('value', flat=True).first()

    # Reactions are submitted asynchronously by the reaction buttons.
    # Returning JSON prevents the browser from navigating/reloading the
    # post page, so the user's scroll position is preserved.
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'like_count': like_count,
            'dislike_count': dislike_count,
            'user_reaction': user_reaction,
        })

    # Keep normal form submissions working as a graceful fallback.
    return redirect('post_detail', slug=post.slug)


def search(request):
    query = request.GET.get('q', '').strip()
    results_qs = Post.objects.none()
    user_results = User.objects.none()

    if query:
        results_qs = Post.objects.filter(
            published_date__lte=timezone.now(), is_removed=False
        ).filter(
            Q(title__icontains=query) | Q(text__icontains=query)
        ).select_related('author').order_by('-published_date')

        user_results = User.objects.filter(
            Q(username__icontains=query) | Q(
                profile__display_name__icontains=query)
        ).select_related('profile').distinct().order_by('username')[:USER_SEARCH_LIMIT]

    paginator = Paginator(results_qs, SEARCH_RESULTS_PER_PAGE)
    results_page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'blog/search_results.html', {
        'query': query,
        'results_page': results_page,
        'user_results': user_results,
    })


def _monthly_interaction_buckets(profile_user, months=12):
    """Comments + reactions on this user's posts, bucketed by month,
    oldest to newest, covering the trailing `months` months. Returns
    pixel-ready values for an SVG bar chart (baseline y=90, max bar
    height 70px) so the template only has to place them, not compute."""
    now = timezone.now()

    buckets = []
    year, month = now.year, now.month
    for _ in range(months):
        buckets.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    buckets.reverse()

    totals = {}
    comment_rows = (
        Comment.objects.filter(post__author=profile_user)
        .annotate(month=TruncMonth('created_date'))
        .values('month').annotate(count=Count('id'))
    )
    reaction_rows = (
        Reaction.objects.filter(post__author=profile_user)
        .annotate(month=TruncMonth('created_date'))
        .values('month').annotate(count=Count('id'))
    )
    for row in list(comment_rows) + list(reaction_rows):
        key = (row['month'].year, row['month'].month)
        totals[key] = totals.get(key, 0) + row['count']

    counts = [totals.get(key, 0) for key in buckets]
    max_count = max(counts) if counts else 0

    baseline_y = 90
    max_bar_height = 70
    bar_width = 22
    slot_width = 30
    start_x = 10

    result = []
    for i, ((year, month), count) in enumerate(zip(buckets, counts)):
        height = round((count / max_count) * max_bar_height) if max_count else 0
        x = start_x + i * slot_width
        result.append({
            'label': date(year, month, 1).strftime('%b'),
            'count': count,
            'x': x,
            'y': baseline_y - height,
            'height': height if height > 0 else 1,
            'label_x': x + bar_width // 2,
        })
    return result


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(
        user=profile_user, defaults={'display_name': profile_user.username})

    posts_qs = Post.objects.filter(
        author=profile_user, published_date__lte=timezone.now(), is_removed=False
    ).order_by('-published_date')

    paginator = Paginator(posts_qs, PROFILE_POSTS_PER_PAGE)
    posts_page = paginator.get_page(request.GET.get('page', 1))

    followers_qs = User.objects.filter(
        following__following=profile_user).select_related('profile')
    following_qs = User.objects.filter(
        followers__follower=profile_user).select_related('profile')

    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user, following=profile_user).exists()

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'posts_page': posts_page,
        'post_count': posts_qs.count(),
        'followers_preview': followers_qs[:FOLLOWERS_PREVIEW_COUNT],
        'followers_count': followers_qs.count(),
        'following_count': following_qs.count(),
        'is_following': is_following,
    }

    if posts_qs.exists():
        context['total_views'] = posts_qs.aggregate(
            total=Sum('view_count'))['total'] or 0
        context['total_likes'] = Reaction.objects.filter(
            post__author=profile_user, value=Reaction.LIKE).count()
        context['total_comments'] = Comment.objects.filter(
            post__author=profile_user).count()

        context['most_popular_post'] = posts_qs.order_by(
            '-view_count').first()
        context['most_liked_post'] = posts_qs.annotate(
            like_total=Count('reactions', filter=Q(reactions__value=Reaction.LIKE))
        ).order_by('-like_total').first()
        context['most_commented_post'] = posts_qs.annotate(
            comment_total=Count('comments')
        ).order_by('-comment_total').first()

        context['interaction_buckets'] = _monthly_interaction_buckets(
            profile_user)

    return render(request, 'blog/profile.html', context)


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user, defaults={'display_name': request.user.username})
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('user_profile', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'blog/profile_edit.html', {'form': form})


@login_required
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target != request.user:
        existing = Follow.objects.filter(
            follower=request.user, following=target).first()
        if existing:
            existing.delete()
        else:
            Follow.objects.create(follower=request.user, following=target)
    return redirect('user_profile', username=username)

# Create your views here.
