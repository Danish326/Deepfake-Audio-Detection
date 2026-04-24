"""
api/dependencies.py

Shared FastAPI dependency functions.

Populated progressively across steps:
  Step 5 — get_current_user (JWT auth dependency)
  Step 3 — get_request_id (read from request.state)

For now this module is a placeholder so imports don't fail.
"""
from fastapi import Request


def get_request_id(request: Request) -> str:
    """Return the request ID injected by RequestIDMiddleware."""
    return getattr(request.state, "request_id", "unknown")
