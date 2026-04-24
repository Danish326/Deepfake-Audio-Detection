"""
api/schemas/predict.py

Request and response schemas for POST /api/v1/predict/audio.

PredictionResponse is the stable API contract — the frontend depends on it.
Contract tests in tests/contract/ verify this shape on every deployment.
"""
from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, Field

from api.schemas.common import BaseResponse


class PerModelOutput(BaseModel):
    """Prediction output from a single ResNet18 model."""
    label:      str   = Field(..., description='"real" or "fake"')
    confidence: float = Field(..., description="max(P(real), P(fake))")
    prob_real:  float = Field(..., description="Softmax probability for real class")
    prob_fake:  float = Field(..., description="Softmax probability for fake class")


class PredictionResponse(BaseResponse):
    """
    Response schema for POST /api/v1/predict/audio.

    Always returned on HTTP 200. Includes:
    - Final label and confidence from the most-confident model
    - Full per-model breakdown across all 8 models
    - Pipeline timing for debugging
    """
    label: str = Field(
        ...,
        description='Final classification: "real" or "fake"',
        examples=["fake"],
    )
    confidence: float = Field(
        ...,
        description="Confidence of the winning model (0.0–1.0)",
        examples=[0.9997],
    )
    prob_real: float = Field(
        ...,
        description="Winning model's probability for real class",
        examples=[0.0003],
    )
    prob_fake: float = Field(
        ...,
        description="Winning model's probability for fake class",
        examples=[0.9997],
    )
    winning_model: str = Field(
        ...,
        description='Which model produced the final prediction, e.g. "mel_data3"',
        examples=["mel_data3"],
    )
    models_ran: int = Field(
        ...,
        description="How many of 8 models contributed to the decision",
        examples=[8],
    )
    per_model: Dict[str, PerModelOutput] = Field(
        ...,
        description="Full output from every model that ran",
    )
    processing_time_ms: float = Field(
        ...,
        description="Total pipeline time in milliseconds (preprocess + 8 inferences)",
        examples=[1684.5],
    )
    filename: Optional[str] = Field(
        default=None,
        description="Original uploaded filename",
    )
    prediction_id: Optional[str] = Field(
        default=None,
        description="Persisted prediction UUID when database storage is enabled",
    )


class PredictionRecord(BaseModel):
    """Stored prediction record returned by retrieval endpoints."""

    prediction_id: str
    label: str
    confidence: float
    prob_real: float
    prob_fake: float
    winning_model: str
    models_ran: int
    processing_time_ms: float
    filename: Optional[str] = None
    request_id: Optional[str] = None
    created_at: str
    per_model: Dict[str, PerModelOutput]


class PredictionHistoryResponse(BaseResponse):
    predictions: list[PredictionRecord]
