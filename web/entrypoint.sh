#!/bin/bash
set -e

mkdir -p /app/staticfiles
chown -R django:django /app/staticfiles
chmod -R 755 /app/staticfiles

echo "Running migrations..."
su django -c "uv run python manage.py migrate"

echo "Loading task statuses and registry fixture..."
su django -c "uv run python manage.py loaddata task_statuses tags workflowregistry" || echo "Warning: Failed to load fixtures, continuing..."

echo "Syncing Badgerdoc API token..."
su django -c "uv run python manage.py shell -c \"import os; from django.contrib.auth.models import User; from rest_framework.authtoken.models import Token; token_value = os.environ.get('BADGERDOC_TOKEN', '').strip(); assert token_value, 'BADGERDOC_TOKEN is empty'; user = User.objects.filter(is_superuser=True).order_by('id').first() or User.objects.order_by('id').first(); assert user is not None, 'No user exists to own BADGERDOC_TOKEN'; updated = Token.objects.filter(user=user).update(key=token_value); updated or Token.objects.create(user=user, key=token_value); print(f'Synced token for user {user.username}')\""

echo "Collecting static files..."
su django -c "uv run python manage.py collectstatic --noinput"

echo "Creating symbolic link to frontend"
su django -c "ln -sf $(pwd)/badgerdoc-frontend $(pwd)/staticfiles/badgerdoc-frontend"

echo "Starting Gunicorn..."
exec su django -c "uv run gunicorn badgerdoc.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --max-requests 1000 \
    --max-requests-jitter 100"
