"""CORS configuration for the pruv API."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# Allowed origins for different environments
ALLOWED_ORIGINS_PRODUCTION = [
    "https://pruv.dev",
    "https://www.pruv.dev",
    "https://app.pruv.dev",
    "https://docs.pruv.dev",
]

ALLOWED_ORIGINS_DEVELOPMENT = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]

ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Request-ID",
    "X-API-Key",
    "X-Chain-ID",
    "X-Idempotency-Key",
    "Accept",
    "Origin",
]

EXPOSED_HEADERS = [
    "X-Request-ID",
    "X-Response-Time",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
]


def get_allowed_origins(environment: str = "development") -> list[str]:
    """Get allowed origins for the given environment."""
    if environment == "production":
        return ALLOWED_ORIGINS_PRODUCTION
    return ALLOWED_ORIGINS_PRODUCTION + ALLOWED_ORIGINS_DEVELOPMENT


class CORSConfig:
    """CORS configuration container."""

    def __init__(self, environment: str = "development") -> None:
        self.allow_origins = get_allowed_origins(environment)
        self.allow_methods = ALLOWED_METHODS
        self.allow_headers = ALLOWED_HEADERS
        self.expose_headers = EXPOSED_HEADERS
        self.allow_credentials = True
        self.max_age = 86400  # 24 hours

    def to_dict(self) -> dict:
        """Convert to dictionary for FastAPI CORSMiddleware."""
        return {
            "allow_origins": self.allow_origins,
            "allow_methods": self.allow_methods,
            "allow_headers": self.allow_headers,
            "expose_headers": self.expose_headers,
            "allow_credentials": self.allow_credentials,
            "max_age": self.max_age,
        }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Strict Transport Security (1 year, include subdomains)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Content Security Policy for API responses
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )

        return response
