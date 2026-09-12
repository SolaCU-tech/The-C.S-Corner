#!/usr/bin/env bash
# Runs on every deploy: install deps, collect static files, run migrations.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input --upload-unhashed-files
python manage.py migrate
