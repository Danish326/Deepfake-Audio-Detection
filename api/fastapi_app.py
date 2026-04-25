"""
api/fastapi_app.py

FastAPI application factory.

Creates and configures the FastAPI application:
  - Loads all 8 ML models at startup via lifespan hook
  - Registers all routers under /v1
  - Adds CORS middleware (origins from CORS_ALLOWED_ORIGINS env var)
  - Adds request-ID and timing middleware
  - Configures OpenAPI docs at /v1/docs

This module is imported by config/asgi.py AFTER Django has been initialised,
so it is safe to use Django ORM here if needed (though routes should stay thin).
"""
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import RequestIDMiddleware, TimingMiddleware
from api.routes.auth import router as auth_router
from api.routes.health import router as health_router
from api.routes.predict import router as predict_router
from api.routes.predictions import router as predictions_router

logger = logging.getLogger("api")


def create_app() -> FastAPI:
    """Construct and return the configured FastAPI application instance."""

    app = FastAPI(
        title="Deepfake Audio Detection API",
        description=(
            "Production backend for deepfake audio detection. "
            "Runs 8 ResNet18 models (4 data batches × 2 feature types) "
            "and returns the most-confident prediction."
        ),
        version="1.0.0",
        # Docs served under /api/v1/... (Starlette strips /api prefix)
        docs_url="/v1/docs",
        redoc_url="/v1/redoc",
        openapi_url="/v1/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────
    _raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    cors_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    # ── Custom middleware (innermost first = executes last) ───
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Routers ───────────────────────────────────────────────
    # All routes are prefixed with /v1 so the full path is /api/v1/...
    app.include_router(health_router,  prefix="/v1")
    app.include_router(auth_router,    prefix="/v1")
    app.include_router(predict_router, prefix="/v1")
    app.include_router(predictions_router, prefix="/v1")

    logger.info("FastAPI application created — docs at /api/v1/docs")
    return app
