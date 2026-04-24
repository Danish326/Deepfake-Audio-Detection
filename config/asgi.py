"""
config/asgi.py

ASGI entry point — mounts Django and FastAPI under a single application.

Routing:
    /api/*   →  FastAPI  (inference API, health, auth endpoints)
    /*       →  Django   (admin panel, Django-served routes)

Django is initialised first (get_asgi_application sets up the ORM and apps).
FastAPI is imported only after Django is ready to avoid model import errors.

Lifespan note:
    When FastAPI is mounted inside a Starlette app, the inner FastAPI lifespan
    hook does NOT fire. The model loading is therefore handled here in the outer
    Starlette lifespan, which does fire on every startup.
"""
import os
import logging
from contextlib import asynccontextmanager

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialise Django — this must happen before any Django model imports.
django_asgi_app = get_asgi_application()

# FastAPI imported after Django is ready.
from api.fastapi_app import create_app  # noqa: E402
from ml.inference.model_registry import load_all_models  # noqa: E402

logger = logging.getLogger("api")

_WEIGHTS_ROOT = os.environ.get("ML_WEIGHTS_ROOT", "ml/weights")


@asynccontextmanager
async def lifespan(app):
    """
    Outer ASGI lifespan — fires for the entire combined application.

    Loads all 8 ML models into the registry before the server starts
    serving traffic. This is the correct place to do it when FastAPI
    is mounted as a sub-application inside Starlette.
    """
    logger.info("[startup] Loading ML models from %s ...", _WEIGHTS_ROOT)
    load_all_models(weights_root=_WEIGHTS_ROOT)
    logger.info("[startup] ML model loading complete.")
    yield
    # Shutdown: models are released with the process — no teardown needed.


fastapi_app = create_app()

# ── Path-based ASGI dispatcher ────────────────────────────────
from starlette.routing import Mount  # noqa: E402
from starlette.applications import Starlette  # noqa: E402

application = Starlette(
    lifespan=lifespan,
    routes=[
        # All /api/* traffic goes to FastAPI.
        # Starlette strips the /api prefix, so FastAPI sees /v1/...
        Mount("/api", app=fastapi_app),
        # Everything else (admin, static, etc.) goes to Django.
        Mount("", app=django_asgi_app),
    ],
)
