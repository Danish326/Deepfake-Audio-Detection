"""
config/settings/staging.py

Staging environment overrides.
- DEBUG = False
- PostgreSQL required (DATABASE_URL must be set)
- Realistic CORS and host restrictions
- Info-level logging
"""
import os
from .base import *  # noqa: F401, F403

# ── No debug in staging ──────────────────────────────────────
DEBUG = False

# ── Staging requires an explicit SECRET_KEY ──────────────────
SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "staging.example.com").split(",")

# ── Staging-specific security headers ───────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
