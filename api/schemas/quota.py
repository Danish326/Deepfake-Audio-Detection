from pydantic import BaseModel, Field
from api.schemas.common import BaseResponse

class PlanSchema(BaseModel):
    name: str = Field(..., description='Plan internal name, e.g. "free"')
    display_name: str = Field(..., description='Plan display name, e.g. "Free Plan"')
    max_predictions_per_month: int = Field(..., description='Limit per month, -1 means unlimited')
    max_audio_duration_seconds: int = Field(..., description='Max audio length allowed')
    max_upload_size_mb: int = Field(..., description='Max file size allowed')
    show_per_model_breakdown: bool = Field(..., description='Whether per_model breakdown is returned')
    price_monthly: str = Field(..., description='Price string')

class UsageSchema(BaseModel):
    predictions_used: int = Field(..., description='Predictions used in current billing period')
    predictions_limit: int = Field(..., description='Predictions limit, -1 means unlimited')
    predictions_remaining: int = Field(..., description='Predictions remaining, -1 means unlimited')
    period_start: str = Field(..., description='Start of billing period (ISO 8601)')
    period_end: str = Field(..., description='End of billing period (ISO 8601)')

class QuotaStatusResponse(BaseResponse):
    plan: PlanSchema
    usage: UsageSchema
