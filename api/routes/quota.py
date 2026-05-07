import logging
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, Request

from api.dependencies import get_current_user
from api.schemas.quota import QuotaStatusResponse
from apps.subscriptions.services import get_quota_status

logger = logging.getLogger("api")
router = APIRouter(tags=["Quota"])

@router.get(
    "/quota/status",
    response_model=QuotaStatusResponse,
    summary="Get Quota Status",
    description="Returns the user's active plan limits and usage for the current billing period."
)
async def get_quota_status_endpoint(
    request: Request,
    user=Depends(get_current_user)
) -> QuotaStatusResponse:
    """Returns the user's current subscription plan and usage."""
    
    status_data = await sync_to_async(get_quota_status)(user)
    request_id = getattr(request.state, "request_id", None)
    
    return QuotaStatusResponse(
        success=True,
        request_id=request_id,
        plan=status_data["plan"],
        usage=status_data["usage"]
    )
