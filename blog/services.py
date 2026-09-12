import requests
from django.core.cache import cache

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

CACHE_KEY = "tech_news"
CACHE_TIMEOUT = 900  # 15 minutes


def get_tech_news(limit=6):
    """Fetch the top 'limit' Hacker News stories.

    Hacker News' API is free, keyless, and squarely tech/CS-relevant,
    so it's a good no-signup fit for this sidebar. Results are cached
    for 15 minutes so we don't hit the API on every single page view.
    If the request fails for any reason (offline, API down, etc.),
    this returns an empty list rather than raising, so a broken news
    feed never takes the rest of the page down with it.
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    try:
        story_ids = requests.get(TOP_STORIES_URL, timeout=3).json()[:limit]
        articles = []
        for story_id in story_ids:
            item = requests.get(ITEM_URL.format(story_id), timeout=3).json()
            if item and item.get('title'):
                articles.append({
                    'title': item['title'],
                    'url': item.get('url') or
                    f"https://news.ycombinator.com/item?id={story_id}",
                })
        cache.set(CACHE_KEY, articles, CACHE_TIMEOUT)
        return articles
    except (requests.RequestException, ValueError, TypeError):
        return []
