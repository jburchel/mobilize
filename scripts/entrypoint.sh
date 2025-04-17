#!/bin/bash
set -e

# Apply database migrations
echo "Applying database migrations..."
flask db upgrade

# Run gunicorn
echo "Starting application with gunicorn..."
exec gunicorn --bind 0.0.0.0:8080 \
    --workers ${GUNICORN_WORKERS:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    wsgi:app 