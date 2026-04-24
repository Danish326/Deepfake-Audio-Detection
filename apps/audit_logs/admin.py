from django.contrib import admin

from apps.audit_logs.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "endpoint", "status_code", "created_at")
    search_fields = ("id", "action", "endpoint")
    list_filter = ("status_code", "created_at")
    readonly_fields = ("id", "created_at")
from django.contrib import admin

# AuditLog admin registration implemented in Step 4.
