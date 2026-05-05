#!/bin/bash
# Stop execution if any command fails
set -e

echo "================================================="
echo "    Deepfake Audio Detection Backend Startup     "
echo "================================================="

# 1. Collect static files (CSS, JS for Admin panel)
echo "[1/3] Collecting static files..."
python manage.py collectstatic --noinput

# 2. Apply database migrations
echo "[2/3] Applying database migrations..."
python manage.py migrate --noinput

# 3. Start the application using Gunicorn + Uvicorn workers
# We use 2 workers here as a good default for a CPU-bound application
# but this can be overridden via environment variables if needed.
echo "[3/3] Starting Gunicorn server..."
exec gunicorn config.asgi:application \
    --name deepfake_audio_backend \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --log-level info \
    --timeout 120
