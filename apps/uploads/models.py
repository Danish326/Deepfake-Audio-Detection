"""
apps/uploads/models.py

UploadedAudio model — stores file metadata for every audio upload.
Full implementation in Step 4.
"""
import uuid

from django.conf import settings
from django.db import models


class UploadedAudio(models.Model):
    """Metadata for each uploaded audio file used in inference."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_audios",
    )
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=128, blank=True, default="")
    file_size_bytes = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "uploaded_audio"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["uploaded_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.file_size_bytes} bytes)"
