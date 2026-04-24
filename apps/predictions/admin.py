from django.contrib import admin
from apps.predictions.models import Prediction, ModelRegistry


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "final_label",
        "final_confidence",
        "winning_model",
        "models_ran",
        "created_at",
    )
    search_fields = ("id", "request_id", "winning_model")
    list_filter = ("final_label", "created_at")
    readonly_fields = ("id", "created_at")


@admin.register(ModelRegistry)
class ModelRegistryAdmin(admin.ModelAdmin):
    list_display = ("model_name", "model_type", "version", "is_active", "created_at")
    list_filter = ("model_type", "is_active", "created_at")
    search_fields = ("model_name", "version", "weight_path")
