"""
apps/predictions/models.py

Prediction model — stores full inference output for every request.

Populated in Step 4. Defined as a placeholder here so the app
is registered in INSTALLED_APPS and migrations can be created.

Key design decisions (implemented in Step 4):
  - UUID primary key for all external-facing IDs
  - Stores per-model probabilities for all 8 models (not just the winner)
  - Stores timing metrics (preprocessing_ms, inference_ms, total_ms)
  - Linked to uploaded_audio via FK — separates file metadata from result
"""
import uuid

from django.conf import settings
from django.db import models


class Prediction(models.Model):
    """Stored inference result for a single audio prediction request."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="predictions",
    )
    uploaded_audio = models.ForeignKey(
        "uploads.UploadedAudio",
        on_delete=models.CASCADE,
        related_name="predictions",
    )

    final_label = models.CharField(max_length=16)
    final_confidence = models.FloatField()
    final_prob_real = models.FloatField()
    final_prob_fake = models.FloatField()
    winning_model = models.CharField(max_length=64)
    models_ran = models.PositiveIntegerField(default=0)
    processing_time_ms = models.FloatField(default=0.0)

    # Stores the full 8-model summary payload returned by the ML layer.
    per_model = models.JSONField(default=dict)
    request_id = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prediction"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["request_id"]),
            models.Index(fields=["final_label"]),
        ]

    def __str__(self) -> str:
        return f"{self.id} - {self.final_label} ({self.final_confidence:.4f})"


class ModelRegistry(models.Model):
    """Tracks model versions and activation state."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=128)
    model_type = models.CharField(max_length=32)  # mel / lfcc
    version = models.CharField(max_length=64)
    weight_path = models.CharField(max_length=512)
    label_map = models.CharField(max_length=128, default="real,fake")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "model_registry"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_type", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.model_name}:{self.version}"
