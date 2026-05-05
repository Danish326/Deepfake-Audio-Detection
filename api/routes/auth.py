import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate
from django.conf import settings

from api.schemas.auth import LoginRequest, TokenResponse, UserResponse
from api.schemas.common import ErrorDetail, ErrorResponse

# We will implement get_current_user in dependencies.py shortly.
from api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

@sync_to_async
def authenticate_user(username, password):
    """
    Validates credentials against Django's authentication backend.
    Runs synchronously but wrapped for async execution.
    """
    return authenticate(username=username, password=password)

def create_access_token(data: dict, expires_delta: timedelta):
    """
    Creates a signed JWT using Django's SECRET_KEY.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}}
)
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    """
    Exchanges valid credentials for a JWT access token.
    """
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Incorrect username or password", "details": {}}
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds())
    )

@router.post("/logout")
async def logout():
    """
    Stub endpoint for client-side logout.
    Since JWTs are stateless, actual token invalidation is handled by the client discarding the token.
    """
    return {"success": True, "message": "Successfully logged out."}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """
    Returns the profile of the currently authenticated user.
    """
    return current_user
