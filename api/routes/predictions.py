from uuid import UUID

from asgiref.sync import sync_to_async
from fastapi import APIRouter, HTTPException, Request, status

from api.schemas.predict import (
    PerModelOutput,
    PredictionHistoryResponse,
    PredictionRecord,
)
from apps.predictions.selectors import get_prediction_by_id, list_predictions

router = APIRouter(tags=["Predictions"])


def _to_record(prediction) -> PredictionRecord:
    per_model = {
        key: PerModelOutput(**vals)
        for key, vals in (prediction.per_model or {}).items()
    }
    return PredictionRecord(
        prediction_id=str(prediction.id),
        label=prediction.final_label,
        confidence=prediction.final_confidence,
        prob_real=prediction.final_prob_real,
        prob_fake=prediction.final_prob_fake,
        winning_model=prediction.winning_model,
        models_ran=prediction.models_ran,
        processing_time_ms=prediction.processing_time_ms,
        filename=prediction.uploaded_audio.original_filename if prediction.uploaded_audio else None,
        request_id=prediction.request_id or None,
        created_at=prediction.created_at.isoformat(),
        per_model=per_model,
    )


@router.get("/predictions/history", response_model=PredictionHistoryResponse)
async def prediction_history(request: Request, limit: int = 20):
    rows = await sync_to_async(list_predictions)(limit=limit)
    return PredictionHistoryResponse(
        success=True,
        request_id=getattr(request.state, "request_id", None),
        predictions=[_to_record(row) for row in rows],
    )


@router.get("/predictions/{prediction_id}", response_model=PredictionRecord)
async def get_prediction(prediction_id: UUID):
    prediction = await sync_to_async(get_prediction_by_id)(prediction_id)
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PREDICTION_NOT_FOUND", "message": "Prediction not found.", "details": {}},
        )
    return _to_record(prediction)
