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
        # Step 3: drop nullability, as its own change.
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(blank=True, max_length=220, null=False),
        ),
        # Step 4: add the uniqueness constraint. Written as raw SQL
        # rather than a normal AlterField — Django's own SQL generator
        # for this exact field/change combination on Postgres emits a
        # genuine duplicate CREATE INDEX statement (confirmed directly
        # via `sqlmigrate`, not a leftover-state issue). The unique
        # constraint below gets its own backing index automatically,
        # same as Django's normal behavior; the extra pattern-matching
        # index Django tries to add isn't needed since nothing in this
        # app queries slug with __startswith/__contains.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='post',
                    name='slug',
                    field=models.SlugField(blank=True, max_length=220, unique=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "blog_post" ADD CONSTRAINT "blog_post_slug_b95473f2_uniq" UNIQUE ("slug");',
                    reverse_sql='ALTER TABLE "blog_post" DROP CONSTRAINT "blog_post_slug_b95473f2_uniq";',
                ),
            ],
        ),
    ]
