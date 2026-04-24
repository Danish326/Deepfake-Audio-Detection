"""
config/settings/local.py

Local development overrides.
- DEBUG = True
- SQLite fallback if DATABASE_URL is not set
- Relaxed host/CORS restrictions
- Verbose console logging
"""
import os
from .base import *  # noqa: F401, F403
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Override: debug on ──────────────────────────────────────
DEBUG = True

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "local-dev-insecure-secret-do-not-use-outside-local",
)

# ── Override: accept all hosts locally ─────────────────────
ALLOWED_HOSTS = ["*"]

# ── Override: SQLite fallback for zero-dependency local start
# If DATABASE_URL is set in .env, dj-database-url already parsed it in base.py.
# Only override when DATABASE_URL is absent.
if not os.environ.get("DATABASE_URL"):
    import dj_database_url  # noqa: F811
    DATABASES = {
        "default": dj_database_url.parse(
            f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
        )
    }

# ── Override: verbose logging ───────────────────────────────
LOGGING["root"]["level"] = "DEBUG"                    # noqa: F405
LOGGING["loggers"]["api"]["level"] = "DEBUG"          # noqa: F405
LOGGING["loggers"]["ml"]["level"] = "DEBUG"           # noqa: F405
LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"  # noqa: F405 — show SQL
