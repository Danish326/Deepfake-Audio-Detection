from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class LoginRequest(BaseModel):
    """Schema for login credentials."""
    username: str
    password: str

class RegisterRequest(BaseModel):
    """Schema for user registration."""
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for a successful JWT token issuance."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Token lifetime in seconds

class UserResponse(BaseModel):
    """Schema for representing the current authenticated user."""
    id: UUID | int | str  # Depending on how Django handles primary keys (usually int for default user, but we'll accept str)
    username: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    is_superuser: bool
    is_active: bool
    date_joined: datetime

    class Config:
        from_attributes = True
