from apps.subscriptions.services import get_user_subscription, get_or_create_usage
from apps.subscriptions.models import Plan
from ml.utils.exceptions import QuotaExceededError, AudioTooLongError, SubscriptionExpiredError

def enforce_quota(user, audio_duration_seconds: float) -> Plan:
    """
    Validates the user's request against their plan limits.
    Called BEFORE inference runs to save compute.
    
    Raises:
        SubscriptionExpiredError: If subscription is not active
        AudioTooLongError: If audio exceeds plan's max duration
        QuotaExceededError: If monthly prediction limit reached
        
    Returns:
        The user's active Plan object (used to check show_per_model_breakdown)
    """
    sub = get_user_subscription(user)
    
    # 1. Check status
    if sub.status != "active":
        raise SubscriptionExpiredError(
            f"Your subscription is {sub.status}. Please renew or contact support."
        )
        
    plan = sub.plan
    
    # 2. Check audio duration
    if audio_duration_seconds > plan.max_audio_duration_seconds:
        raise AudioTooLongError(
            f"Audio duration {audio_duration_seconds:.1f}s exceeds your plan's limit of {plan.max_audio_duration_seconds}s. Upgrade for longer audio."
        )
        
    # 3. Check prediction count
    if plan.max_predictions_per_month != -1:  # -1 is unlimited
        usage = get_or_create_usage(user)
        if usage.predictions_used >= plan.max_predictions_per_month:
            raise QuotaExceededError(
                f"You have used all {plan.max_predictions_per_month} predictions for this billing period. Upgrade your plan for more."
            )
            
    return plan
