import uuid
from django.conf import settings
from django.db import models


class Plan(models.Model):
    """Defines available subscription plans and their limits."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=128)
    
    # Quotas (-1 means unlimited)
    max_predictions_per_month = models.IntegerField(default=5)
    max_audio_duration_seconds = models.IntegerField(default=60)
    max_upload_size_mb = models.IntegerField(default=20)
    
    # Features
    show_per_model_breakdown = models.BooleanField(default=False)
    
    # Billing
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plan"
        ordering = ["price_monthly"]

    def __str__(self) -> str:
        return self.display_name


class Subscription(models.Model):
    """Links a user to a specific plan. One active subscription per user."""
    STATUS_CHOICES = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active")
    
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} - {self.plan.display_name} ({self.status})"


class UsageRecord(models.Model):
    """Tracks a user's predictions within a specific 30-day billing window."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_records"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="usage_records"
    )
    
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    predictions_used = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "usage_record"
        ordering = ["-period_end"]
        indexes = [
            models.Index(fields=["user", "period_start", "period_end"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.predictions_used} used ({self.period_start.date()} to {self.period_end.date()})"
