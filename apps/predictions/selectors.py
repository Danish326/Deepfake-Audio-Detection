from apps.predictions.models import Prediction


def get_prediction_by_id(prediction_id):
    return (
        Prediction.objects.select_related("uploaded_audio")
        .filter(id=prediction_id)
        .first()
    )


def list_predictions(user, limit: int = 20):
    qs = Prediction.objects.select_related("uploaded_audio").filter(user=user).order_by("-created_at")
    if limit > 0:
        return list(qs[:limit])
    return list(qs)
