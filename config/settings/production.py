"""
config/settings/production.py

Production environment overrides.
- DEBUG = False  (enforced — never read from env)
- All secrets MUST be set via environment variables
- Full security hardening
- HTTPS enforcement
"""
import os
from .base import *  # noqa: F401, F403

# ── Hard off — never allow debug in production ────────────────
DEBUG = False

# ── Required — will raise KeyError at startup if missing ──────
SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")

# ── HTTPS enforcement ─────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000        # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ── Security headers ──────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ── Production logging: JSON formatter ───────────────────────
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405
