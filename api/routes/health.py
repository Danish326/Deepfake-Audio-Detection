"""
api/routes/health.py

GET /api/v1/health — service liveness and readiness check.

Step 1: returned a stub with all model flags False.
Step 2 (this file): reads real load status from ml.inference.model_registry.
"""
import logging
from asgiref.sync import sync_to_async
from django.db import connection

from fastapi import APIRouter, Request
from api.schemas.common import HealthResponse
from ml.inference.model_registry import get_load_status, all_models_loaded

logger = logging.getLogger("api")
router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Returns the operational status of the service. "
        "Reports real load status for all 8 ML models. "
        "Database connectivity check added in Step 3."
    ),
)
async def health_check(request: Request) -> HealthResponse:
    """
    Liveness + readiness probe.

    - `status`: "ok" when all 8 models are loaded; "degraded" when some are missing.
    - `models`: Per-model boolean load status (real values from registry).
    - `database`: "unknown" until Step 3 adds the connectivity check.
    """
    request_id = getattr(request.state, "request_id", None)
    load_status = get_load_status()
    all_ok = all_models_loaded()

    # ── Database Check ──
    db_status = "ok"
    try:
        await sync_to_async(connection.ensure_connection)()
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        db_status = "error"
        all_ok = False  # Degrade overall status if DB is down

    return HealthResponse(
        success=True,
        status="ok" if all_ok else "degraded",
        service="deepfake-audio-backend",
        models=load_status,
        database=db_status,
        version="1.0.0",
        request_id=request_id,
    )
