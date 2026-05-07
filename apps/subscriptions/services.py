import logging
from datetime import timedelta
from django.utils import timezone
from apps.subscriptions.models import Plan, Subscription, UsageRecord

logger = logging.getLogger("apps")

def get_free_plan() -> Plan:
    """Returns the default Free plan, creating it if it doesn't exist (failsafe)."""
    plan, _ = Plan.objects.get_or_create(
        name="free",
        defaults={
            "display_name": "Free Plan",
            "max_predictions_per_month": 5,
            "max_audio_duration_seconds": 60,
            "max_upload_size_mb": 20,
            "show_per_model_breakdown": False,
            "price_monthly": 0.00,
        }
    )
    return plan

def get_user_subscription(user) -> Subscription:
    """
    Returns the user's active subscription. 
    If they don't have one, creates one on the Free plan.
    """
    # Check if they already have one
    if hasattr(user, 'subscription'):
        return user.subscription

    # Otherwise, assign the Free plan
    free_plan = get_free_plan()
    sub = Subscription.objects.create(
        user=user,
        plan=free_plan,
        status="active"
    )
    logger.info("Auto-assigned Free plan to user %s", user.id)
    return sub

def get_user_plan(user) -> Plan:
    """Convenience method to just get the plan."""
    return get_user_subscription(user).plan

def get_or_create_usage(user) -> UsageRecord:
    """
    Returns the UsageRecord for the current 30-day rolling window.
    The window starts from the user's account creation date.
    """
    sub = get_user_subscription(user)
    now = timezone.now()
    
    # Calculate current period start based on user.created_at
    # We use 30-day rolling windows
    delta = now - user.created_at
    periods_elapsed = delta.days // 30
    
    current_period_start = user.created_at + timedelta(days=periods_elapsed * 30)
    current_period_end = current_period_start + timedelta(days=30)
    
    # Get or create the usage record for this specific period
    usage, created = UsageRecord.objects.get_or_create(
        user=user,
        subscription=sub,
        period_start=current_period_start,
        period_end=current_period_end,
        defaults={"predictions_used": 0}
    )
    
    if created:
        logger.info("Started new billing period for user %s (period %d)", user.id, periods_elapsed + 1)
        
    return usage

def increment_usage(user) -> None:
    """Increments the prediction count for the current period."""
    usage = get_or_create_usage(user)
    usage.predictions_used += 1
    usage.save(update_fields=["predictions_used", "updated_at"])

def get_quota_status(user) -> dict:
    """Returns a structured dict for the quota/status API."""
    sub = get_user_subscription(user)
    plan = sub.plan
    usage = get_or_create_usage(user)
    
    predictions_remaining = -1
    if plan.max_predictions_per_month != -1:
        predictions_remaining = max(0, plan.max_predictions_per_month - usage.predictions_used)
        
    return {
        "plan": {
            "name": plan.name,
            "display_name": plan.display_name,
            "max_predictions_per_month": plan.max_predictions_per_month,
            "max_audio_duration_seconds": plan.max_audio_duration_seconds,
            "max_upload_size_mb": plan.max_upload_size_mb,
            "show_per_model_breakdown": plan.show_per_model_breakdown,
            "price_monthly": str(plan.price_monthly),
        },
        "usage": {
            "predictions_used": usage.predictions_used,
            "predictions_limit": plan.max_predictions_per_month,
            "predictions_remaining": predictions_remaining,
            "period_start": usage.period_start.isoformat(),
            "period_end": usage.period_end.isoformat(),
        }
    }
