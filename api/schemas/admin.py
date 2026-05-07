from typing import List, Optional
from pydantic import BaseModel, EmailStr
from api.schemas.common import BaseResponse
from api.schemas.predict import PredictionRecord

class UserAdminRecord(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_staff: bool
    created_at: str

class AdminUsersResponse(BaseResponse):
    users: List[UserAdminRecord]
    total_users: int

class AdminPredictionsResponse(BaseResponse):
    predictions: List[PredictionRecord]
    total_predictions: int

class AdminStatsResponse(BaseResponse):
    total_users: int
    total_predictions: int
    total_audio_duration_seconds: float
