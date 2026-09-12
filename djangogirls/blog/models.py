from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True, db_index=True)
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    image = models.ImageField(
        upload_to='post_images/', blank=True, null=True)
    is_removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='removed_posts')

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:200] or 'post'
            slug = base_slug
            counter = 2
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField(max_length=1000)
    created_date = models.DateTimeField(default=timezone.now)
    is_removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='removed_comments')

    class Meta:
        ordering = ['created_date']

    def __str__(self):
        return f"{self.author.username} on {self.post.title}"


class Reaction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    VALUE_CHOICES = [(LIKE, 'Like'), (DISLIKE, 'Dislike')]

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.CharField(max_length=7, choices=VALUE_CHOICES)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} {self.value}d {self.post.title}"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=False)
    real_name = models.CharField(max_length=100, blank=True)
    bio = models.CharField(max_length=300, blank=True)
    university = models.CharField(max_length=150, blank=True)
    current_level = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class PostRead(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='read_posts')
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='read_by')
    read_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'post')


from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance, defaults={'display_name': instance.username})

# Create your models here.
