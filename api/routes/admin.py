import logging
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, Request
from django.contrib.auth import get_user_model
from django.db.models import Sum

from api.dependencies import get_current_admin_user
from api.schemas.admin import AdminUsersResponse, AdminPredictionsResponse, AdminStatsResponse, UserAdminRecord
from apps.predictions.models import Prediction
from api.routes.predictions import _to_record

logger = logging.getLogger("api")
router = APIRouter(tags=["Admin"])
User = get_user_model()


def get_all_users(limit=50):
    return list(User.objects.all().order_by("-created_at")[:limit])

def get_all_predictions(limit=50):
    qs = Prediction.objects.select_related("uploaded_audio").all().order_by("-created_at")
    if limit > 0:
        return list(qs[:limit])
    return list(qs)

def get_stats():
    total_users = User.objects.count()
    total_predictions = Prediction.objects.count()
    # If audio duration is stored, we could sum it. We'll leave it 0 for now.
    return total_users, total_predictions


@router.get("/admin/users", response_model=AdminUsersResponse)
async def list_users_admin(request: Request, limit: int = 50, admin_user=Depends(get_current_admin_user)):
    users = await sync_to_async(get_all_users)(limit=limit)
    total_users = await sync_to_async(User.objects.count)()
    
    records = [
        UserAdminRecord(
            id=str(u.id),
            username=u.username,
            email=u.email,
            is_active=u.is_active,
            is_staff=u.is_staff,
            created_at=u.created_at.isoformat()
        )
        for u in users
    ]
    return AdminUsersResponse(
        success=True,
        request_id=getattr(request.state, "request_id", None),
        users=records,
        total_users=total_users
    )


@router.get("/admin/predictions", response_model=AdminPredictionsResponse)
async def list_predictions_admin(request: Request, limit: int = 50, admin_user=Depends(get_current_admin_user)):
    predictions = await sync_to_async(get_all_predictions)(limit=limit)
    total_predictions = await sync_to_async(Prediction.objects.count)()
    
    records = [_to_record(p) for p in predictions]
    return AdminPredictionsResponse(
        success=True,
        request_id=getattr(request.state, "request_id", None),
        predictions=records,
        total_predictions=total_predictions
    )


@router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(request: Request, admin_user=Depends(get_current_admin_user)):
    total_users, total_predictions = await sync_to_async(get_stats)()
    return AdminStatsResponse(
        success=True,
        request_id=getattr(request.state, "request_id", None),
        total_users=total_users,
        total_predictions=total_predictions,
        total_audio_duration_seconds=0.0
    )
