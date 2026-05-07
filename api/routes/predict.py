"""
api/routes/predict.py

POST /api/v1/predict/audio

Accepts a multipart/form-data audio file upload, validates it, runs the full
ML inference pipeline, and returns a structured prediction response.

Pipeline (all synchronous):
    1. Receive UploadFile
    2. Read all bytes into memory (no temp files written to disk)
    3. Validate extension and size
    4. Call ml.inference.predictor.predict(audio_bytes)
    5. Map AggregatedResult → PredictionResponse → return

No database persistence (Step 4) and no auth (Step 5) in this version.
"""
import time
import logging
import os
from pathlib import Path

from asgiref.sync import sync_to_async
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, status, Depends

from api.dependencies import get_request_id, get_current_user
from api.schemas.predict import PredictionResponse, PerModelOutput
from api.schemas.common import ErrorDetail, ErrorResponse
from apps.predictions.services import create_prediction_record
from apps.subscriptions.quota import enforce_quota
from apps.subscriptions.services import increment_usage
from ml.inference.predictor import predict
from ml.preprocessing.audio_io import get_audio_duration
from ml.utils.constants import (
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
)
from ml.utils.exceptions import (
    AudioLoadError,
    FeatureExtractionError,
    ModelNotLoadedError,
    QuotaExceededError,
    AudioTooLongError,
    SubscriptionExpiredError,
)

logger = logging.getLogger("api")
router = APIRouter(tags=["Inference"])


def _validate_file(filename: str, content_length: int | None) -> None:
    """
    Run fast pre-checks before touching the file content.

    Args:
        filename:       Original filename from the upload.
        content_length: Declared Content-Length (may be None).

    Raises:
        HTTPException 400: If extension is unsupported or declared size exceeds limit.
    """
    ext = Path(filename).suffix.lower() if filename else ""
    if not ext or ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorDetail(
                code="INVALID_FILE_TYPE",
                message=(
                    f"Unsupported file type '{ext}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
                ),
            ).model_dump(),
        )

    # Quick check on declared size (not always present)
    if content_length and content_length > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorDetail(
                code="FILE_TOO_LARGE",
                message=f"File exceeds the {MAX_UPLOAD_SIZE_MB} MB limit.",
            ).model_dump(),
        )


@router.post(
    "/predict/audio",
    response_model=PredictionResponse,
    summary="Detect Deepfake Audio",
    description=(
        "Upload an audio file (`.wav`, `.mp3`, or `.flac`) and receive a real/fake "
        "prediction. Runs 8 ResNet18 models (4 data batches × 2 feature types) and "
        "returns the most-confident prediction along with a full per-model breakdown."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type or file too large"},
        500: {"model": ErrorResponse, "description": "Internal inference error"},
        503: {"model": ErrorResponse, "description": "Models not loaded"},
    },
)
async def predict_audio(
    file: UploadFile = File(..., description="Audio file to analyse (.wav / .mp3 / .flac)"),
    request_id: str = Depends(get_request_id),
    user = Depends(get_current_user),
) -> PredictionResponse:
    """
    Deepfake audio detection endpoint.

    **Steps:**
    1. Validates file extension and size.
    2. Reads audio bytes into memory.
    3. Runs the full preprocessing pipeline (decode → 5s normalise → mel + LFCC).
    4. Passes both feature tensors through all 8 ResNet18 models.
    5. Selects the most-confident prediction (most-confident-wins aggregation).
    6. Returns final label, confidence, and full per-model breakdown.
    """
    t_start = time.perf_counter()

    # ── Step 1: Pre-check filename and declared Content-Length ──
    _validate_file(
        filename=file.filename or "",
        content_length=file.size,
    )

    # ── Step 2: Read bytes ───────────────────────────────────────
    audio_bytes = await file.read()

    # ── Step 3: Check actual size ────────────────────────────────
    if len(audio_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorDetail(
                code="FILE_TOO_LARGE",
                message=f"File size {len(audio_bytes) / (1024*1024):.1f} MB exceeds the {MAX_UPLOAD_SIZE_MB} MB limit.",
            ).model_dump(),
        )

    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorDetail(
                code="EMPTY_FILE",
                message="The uploaded file is empty.",
            ).model_dump(),
        )

    logger.info(
        "predict/audio: file=%s  size=%.1f KB  request_id=%s",
        file.filename,
        len(audio_bytes) / 1024,
        request_id,
    )

    # ── Step 3.5: Enforce Quota ──────────────────────────────────
    try:
        # Fast check for duration before ML runs
        duration = await sync_to_async(get_audio_duration)(audio_bytes)
        plan = await sync_to_async(enforce_quota)(user, duration)
    except (QuotaExceededError, AudioTooLongError, SubscriptionExpiredError) as exc:
        logger.warning("Quota rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorDetail(
                code="QUOTA_EXCEEDED",
                message=str(exc),
            ).model_dump(),
        )

    # ── Step 4: Run inference ────────────────────────────────────
    try:
        result = predict(audio_bytes)

    except ModelNotLoadedError as exc:
        logger.error("Models unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorDetail(
                code="MODELS_UNAVAILABLE",
                message="ML models are not loaded. Check server startup logs.",
            ).model_dump(),
        )

    except AudioLoadError as exc:
        logger.warning("Invalid audio: %s  file=%s", exc, file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorDetail(
                code="INVALID_AUDIO",
                message=f"Could not decode audio file: {exc}",
            ).model_dump(),
        )

    except (FeatureExtractionError, Exception) as exc:
        logger.exception("Inference error for file=%s: %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="INFERENCE_ERROR",
                message="An internal error occurred during inference. Please try again.",
            ).model_dump(),
        )

    # ── Step 4.5: Increment Usage ────────────────────────────────
    await sync_to_async(increment_usage)(user)

    # ── Step 5: Persist result (Step 4) ──────────────────────────
    total_ms = (time.perf_counter() - t_start) * 1000
    content_type = file.content_type or ""
    prediction_row = await sync_to_async(create_prediction_record)(
        result=result,
        filename=file.filename or "unknown",
        file_size_bytes=len(audio_bytes),
        mime_type=content_type,
        request_id=request_id,
        processing_time_ms=round(total_ms, 2),
        user=user,
    )

    # ── Step 6: Build response ───────────────────────────────────

    per_model = {}
    if plan.show_per_model_breakdown:
        per_model = {
            key: PerModelOutput(
                label=vals["label"],
                confidence=vals["confidence"],
                prob_real=vals["prob_real"],
                prob_fake=vals["prob_fake"],
            )
            for key, vals in result.per_model_summary.items()
        }

    return PredictionResponse(
        success=True,
        request_id=request_id,
        label=result.label,
        confidence=result.confidence,
        prob_real=result.prob_real,
        prob_fake=result.prob_fake,
        winning_model=result.winning_model,
        models_ran=len(result.all_outputs),
        per_model=per_model,
        processing_time_ms=round(total_ms, 2),
        filename=file.filename,
        prediction_id=str(prediction_row.id),
    )
