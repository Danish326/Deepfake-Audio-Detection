from apps.predictions.models import Prediction


def get_prediction_by_id(prediction_id):
    return (
        Prediction.objects.select_related("uploaded_audio")
        .filter(id=prediction_id)
        .first()
    )


def list_predictions(limit: int = 20):
    safe_limit = max(1, min(limit, 100))
    return list(Prediction.objects.select_related("uploaded_audio").all()[:safe_limit])
