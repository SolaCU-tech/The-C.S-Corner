from django.db import migrations, models
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    Post = apps.get_model('blog', 'Post')
    for post in Post.objects.filter(slug__isnull=True) | Post.objects.filter(slug=''):
        base_slug = slugify(post.title)[:200] or 'post'
        slug = base_slug
        counter = 2
        while Post.objects.filter(slug=slug).exclude(pk=post.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        post.slug = slug
        post.save(update_fields=['slug'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_alter_post_published_date_alter_post_view_count'),
    ]

    operations = [
        # Step 1: add the column without a uniqueness constraint yet, so
        # this succeeds even though every existing row starts blank.
        migrations.AddField(
            model_name='post',
            name='slug',
            field=models.SlugField(blank=True, max_length=220, null=True, default=None),
        ),
        # Step 2: give every existing post a real, unique slug.
        migrations.RunPython(backfill_slugs, noop_reverse),
        # Step 3: now that every row has a unique value, it's safe to
        # enforce uniqueness going forward.
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(blank=True, max_length=220, unique=True),
        ),
    ]
