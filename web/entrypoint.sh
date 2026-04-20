#!/bin/bash
set -e

mkdir -p /app/staticfiles
chown -R django:django /app/staticfiles
chmod -R 755 /app/staticfiles

echo "Running migrations..."
su django -c "uv run python manage.py migrate"

echo "Loading task statuses and registry fixture..."
su django -c "uv run python manage.py loaddata task_statuses tags workflowregistry" || echo "Warning: Failed to load fixtures, continuing..."

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
