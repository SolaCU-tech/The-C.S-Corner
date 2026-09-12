#!/usr/bin/env bash
# Runs on every deploy: install deps, collect static files, run migrations.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input --upload-unhashed-files

# Migrations run against the direct (non-pooled) connection when
# available — Neon's pooled connection can behave inconsistently with
# Django's migration executor. Runtime app traffic keeps using the
# normal pooled DATABASE_URL, set separately below.
if [ -n "$DIRECT_DATABASE_URL" ]; then
    DATABASE_URL="$DIRECT_DATABASE_URL" python manage.py migrate
else
    python manage.py migrate
fi
