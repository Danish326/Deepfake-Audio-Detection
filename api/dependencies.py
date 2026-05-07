"""
api/dependencies.py

Shared FastAPI dependency functions.

Populated progressively across steps:
  Step 5 — get_current_user (JWT auth dependency)
  Step 3 — get_request_id (read from request.state)

For now this module is a placeholder so imports don't fail.
"""
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

User = get_user_model()

@sync_to_async
def get_user_by_id(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None
def get_request_id(request: Request) -> str:
    """Return the request ID injected by RequestIDMiddleware."""
    return getattr(request.state, "request_id", "unknown")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the JWT token and returns the current Django User.
    Raises 401 Unauthorized if token is invalid or user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "INVALID_TOKEN", "message": "Could not validate credentials", "details": {}},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Token has expired", "details": {}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INACTIVE_USER", "message": "Inactive user account", "details": {}},
        )
    return user

async def get_current_admin_user(user = Depends(get_current_user)):
    """
    Validates that the current user has admin privileges.
    """
    if not (user.is_staff or user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin privileges required", "details": {}},
        )
    return user
