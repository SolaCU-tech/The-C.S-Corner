from django.utils import timezone
from .facts import get_random_tidbit
from .services import get_tech_news


def cs_tidbit(request):
    return {'cs_tidbit': get_random_tidbit()}


def tech_news(request):
    return {'tech_news': get_tech_news()}


def nav_profile_stats(request):
    if not request.user.is_authenticated:
        return {}

    from .models import Post

    return {
        'nav_followers_count': request.user.followers.count(),
        'nav_following_count': request.user.following.count(),
        'nav_post_count': Post.objects.filter(
            author=request.user, published_date__lte=timezone.now()).count(),
    }
