from typing import Optional

from apps.predictions.models import Prediction
from apps.uploads.models import UploadedAudio
from ml.inference.aggregator import AggregatedResult


def create_prediction_record(
    *,
    result: AggregatedResult,
    filename: str,
    file_size_bytes: int,
    mime_type: str = "",
    request_id: Optional[str] = None,
    processing_time_ms: float = 0.0,
    user=None,
) -> Prediction:
    """Persist upload metadata and aggregated inference output."""
    uploaded_audio = UploadedAudio.objects.create(
        user=user,
        original_filename=filename[:255],
        mime_type=(mime_type or "")[:128],
        file_size_bytes=file_size_bytes,
    )

    prediction = Prediction.objects.create(
        user=user,
        uploaded_audio=uploaded_audio,
        final_label=result.label,
        final_confidence=result.confidence,
        final_prob_real=result.prob_real,
        final_prob_fake=result.prob_fake,
        winning_model=result.winning_model,
        models_ran=len(result.all_outputs),
        processing_time_ms=processing_time_ms,
        per_model=result.per_model_summary,
        request_id=(request_id or "")[:128],
    )
    return prediction
