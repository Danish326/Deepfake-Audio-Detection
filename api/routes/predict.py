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
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, status

from api.schemas.predict import PredictionResponse, PerModelOutput
from api.schemas.common import ErrorDetail, ErrorResponse
from apps.predictions.services import create_prediction_record
from ml.inference.predictor import predict
from ml.utils.constants import (
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
)
from ml.utils.exceptions import (
    AudioLoadError,
    FeatureExtractionError,
    ModelNotLoadedError,
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
    request: Request,
    file: UploadFile = File(..., description="Audio file to analyse (.wav / .mp3 / .flac)"),
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
    request_id = getattr(request.state, "request_id", None)
    t_start = time.perf_counter()

    # ── Step 1: Pre-check filename and declared Content-Length ──
    _cl = request.headers.get("content-length")
    _validate_file(
        filename=file.filename or "",
        content_length=int(_cl) if _cl and _cl.isdigit() else None,
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
    )

    # ── Step 6: Build response ───────────────────────────────────

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
