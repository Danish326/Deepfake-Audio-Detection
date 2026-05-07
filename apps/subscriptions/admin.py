from django.contrib import admin
from apps.subscriptions.models import Plan, Subscription, UsageRecord

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "max_predictions_per_month", "max_audio_duration_seconds", "price_monthly", "is_active")
    list_filter = ("is_active", "show_per_model_breakdown")
    search_fields = ("name", "display_name")

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "started_at", "expires_at")
    list_filter = ("status", "plan")
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)

@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "period_start", "period_end", "predictions_used")
    list_filter = ("period_start", "period_end")
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user", "subscription")
    readonly_fields = ("predictions_used", "period_start", "period_end", "user", "subscription")
