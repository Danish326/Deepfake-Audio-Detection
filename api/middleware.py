"""
api/middleware.py

Custom Starlette middleware for the FastAPI inference layer.

RequestIDMiddleware  — injects a unique X-Request-ID into every request/response.
TimingMiddleware     — measures end-to-end request latency and returns it as
                       X-Process-Time-Ms response header.

Both middleware classes expose their values via request.state so that route
handlers can access them without re-reading headers.
"""
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Inject a unique request ID into every request.

    If the caller sends an X-Request-ID header, that value is reused
    (useful for end-to-end correlation with the frontend). Otherwise a
    fresh UUID4 is generated.

    The ID is:
      - stored on request.state.request_id
      - echoed back in the X-Request-ID response header
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Measure total request processing time.

    The elapsed time (in milliseconds, 2 decimal places) is stored on
    request.state.process_time_ms and returned as X-Process-Time-Ms.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        request.state.process_time_ms = elapsed_ms
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response
