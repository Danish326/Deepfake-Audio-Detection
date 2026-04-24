"""
config/wsgi.py

WSGI entry point — optional fallback for non-ASGI deployments.
For production, prefer config.asgi:application with Uvicorn/Gunicorn.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
