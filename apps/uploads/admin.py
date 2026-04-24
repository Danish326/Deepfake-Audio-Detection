from django.contrib import admin

from apps.uploads.models import UploadedAudio


@admin.register(UploadedAudio)
class UploadedAudioAdmin(admin.ModelAdmin):
    list_display = ("id", "original_filename", "file_size_bytes", "uploaded_at")
    search_fields = ("id", "original_filename", "mime_type")
    list_filter = ("uploaded_at",)
    readonly_fields = ("id", "uploaded_at")
