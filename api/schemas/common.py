"""
api/schemas/common.py

Shared Pydantic response models used across multiple routes.

All API responses follow a consistent shape:
  {
    "success": true | false,
    "request_id": "optional-correlation-id",
    ...
  }

This contract must remain stable across releases — the frontend depends on it.
Contract tests in tests/contract/ verify this shape on every deployment.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────────────────────
class BaseResponse(BaseModel):
    """Root response shape inherited by all API responses."""
    success: bool
    request_id: Optional[str] = Field(default=None, description="Client-provided or server-generated correlation ID")


# ─────────────────────────────────────────────────────────────
# ERROR
# ─────────────────────────────────────────────────────────────
class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code, e.g. INVALID_AUDIO_FORMAT")
    message: str = Field(..., description="Human-readable description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Optional extra context")


class ErrorResponse(BaseResponse):
    """Returned whenever success=false."""
    success: bool = False
    error: ErrorDetail


# ─────────────────────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────────────────────
class ModelStatus(BaseModel):
    """Per-feature-type model load status across all 4 batches."""
    mel_data3: bool = False
    mel_data5: bool = False
    mel_data6: bool = False
    mel_data8: bool = False
    lfcc_data3: bool = False
    lfcc_data5: bool = False
    lfcc_data6: bool = False
    lfcc_data8: bool = False

    @property
    def all_loaded(self) -> bool:
        return all(self.model_dump().values())


class HealthResponse(BaseResponse):
    """
    Response schema for GET /api/v1/health.

    In Step 1 this returns a stub. Steps 2–3 expand it to check
    actual model load status and DB connectivity.
    """
    status: str = Field(..., description="ok | degraded | down")
    service: str = Field(default="deepfake-audio-backend")
    models: Dict[str, bool] = Field(
        default_factory=dict,
        description="Load status for each of the 8 models (populated Step 2)"
    )
    database: str = Field(default="unknown", description="ok | error | unknown")
    version: str = Field(default="1.0.0")
