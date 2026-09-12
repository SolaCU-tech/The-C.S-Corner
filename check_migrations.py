from django.db import connection
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()


cur = connection.cursor()
cur.execute("DROP INDEX IF EXISTS blog_post_slug_b95473f2_like")
print("Cleaned up.")
