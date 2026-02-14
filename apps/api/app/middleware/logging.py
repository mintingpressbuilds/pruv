"""Request logging middleware for the pruv API."""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("pruv.api.access")

# Patterns to redact from log error messages
_SECRET_PATTERNS = [
    re.compile(r"sk_(?:live|test)_[a-zA-Z0-9]+"),
    re.compile(r"pv_(?:live|test)_[a-zA-Z0-9_-]+"),
    re.compile(r"ghp_[a-zA-Z0-9]+"),
    re.compile(r"gho_[a-zA-Z0-9]+"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"xoxb-[a-zA-Z0-9-]+"),
    re.compile(r"Bearer\s+\S+"),
    re.compile(r"(?:password|secret|token|api_key)\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"(?:postgresql|postgres|mysql|mongodb|redis)://\S+"),
]


def _redact_secrets(text: str) -> str:
    """Remove known secret patterns from a string."""
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request details as structured JSON."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.monotonic()

        # Extract request metadata
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        try:
            response = await call_next(request)
            duration_ms = (time.monotonic() - start_time) * 1000

            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Inject rate limit headers if set by dependency
            if hasattr(request.state, "rate_limit_headers"):
                for header, value in request.state.rate_limit_headers.items():
                    response.headers[header] = value

            # Log structured JSON
            _log_request(
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            return response

        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            _log_request(
                request_id=request_id,
                method=method,
                path=path,
                status_code=500,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
                error=_redact_secrets(str(exc)),
            )
            raise


def _log_request(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: str,
    user_agent: str,
    error: str | None = None,
) -> None:
    """Log a structured request entry as JSON."""
    log_entry = {
        "timestamp": time.time(),
        "level": "error" if status_code >= 500 else ("warn" if status_code >= 400 else "info"),
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "client_ip": client_ip,
        "user_agent": user_agent,
    }
    if error:
        log_entry["error"] = error

    # Output structured JSON to stdout
    log_line = json.dumps(log_entry, separators=(",", ":"))
    logger.info(log_line)

    # Buffer for admin endpoint
    _request_log_buffer.append(log_entry)
    if len(_request_log_buffer) > _MAX_LOG_BUFFER:
        _request_log_buffer.pop(0)


# In-memory log buffer for admin endpoints
_request_log_buffer: list[dict] = []
_MAX_LOG_BUFFER = 10000


def get_recent_logs(limit: int = 100) -> list[dict]:
    """Get recent request logs."""
    return _request_log_buffer[-limit:]


def get_slow_requests(threshold_ms: float = 1000.0, limit: int = 50) -> list[dict]:
    """Get requests slower than threshold."""
    slow = [
        log for log in _request_log_buffer
        if log["duration_ms"] > threshold_ms
    ]
    return slow[-limit:]


def get_error_requests(limit: int = 50) -> list[dict]:
    """Get requests that resulted in errors."""
    errors = [
        log for log in _request_log_buffer
        if log["status_code"] >= 400
    ]
    return errors[-limit:]


def get_request_stats() -> dict:
    """Get aggregate request statistics."""
    if not _request_log_buffer:
        return {
            "total_requests": 0,
            "avg_duration_ms": 0,
            "error_rate": 0,
            "status_codes": {},
        }

    total = len(_request_log_buffer)
    avg_duration = sum(log["duration_ms"] for log in _request_log_buffer) / total
    errors = sum(1 for log in _request_log_buffer if log["status_code"] >= 400)

    status_codes: dict[str, int] = {}
    for log in _request_log_buffer:
        code = str(log["status_code"])
        status_codes[code] = status_codes.get(code, 0) + 1

    return {
        "total_requests": total,
        "avg_duration_ms": round(avg_duration, 2),
        "error_rate": round(errors / total, 4),
        "status_codes": status_codes,
    }


# Configure structured JSON logging to stdout
def _setup_logging() -> None:
    """Configure the pruv API logger for structured JSON output."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    api_logger = logging.getLogger("pruv.api")
    api_logger.addHandler(handler)
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False


_setup_logging()
