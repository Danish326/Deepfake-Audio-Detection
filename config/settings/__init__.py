"""
config/settings/__init__.py

Selects the correct settings module based on the APP_ENV environment variable.
Load order: .env file → APP_ENV → import correct settings module.

Valid values for APP_ENV:
    local       (default) — SQLite, DEBUG=True, relaxed security
    staging     — PostgreSQL, DEBUG=False, realistic env
    production  — PostgreSQL, DEBUG=False, fully hardened
"""
import os
from dotenv import load_dotenv

# Load the .env file from the project root before anything else reads env vars.
# This is a no-op in production where env vars are injected by the platform.
load_dotenv()

_env = os.environ.get("APP_ENV", "local").lower()

if _env == "production":
    from .production import *          # noqa: F401, F403
elif _env == "staging":
    from .staging import *             # noqa: F401, F403
else:
    from .local import *               # noqa: F401, F403
