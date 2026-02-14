"""Application configuration."""

from __future__ import annotations

import logging
import os
import secrets
import warnings
from dataclasses import dataclass

logger = logging.getLogger("pruv.api.config")


@dataclass
class Settings:
    """Application settings loaded from environment."""

    # App
    app_name: str = "pruv API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = ""
    database_pool_size: int = 10

    # Redis
    redis_url: str = ""

    # Auth
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""

    # Rate limiting
    rate_limit_free: int = 60  # requests per minute
    rate_limit_pro: int = 300
    rate_limit_team: int = 1000

    # Entry limits per month
    entry_limit_free: int = 1000
    entry_limit_pro: int = 50000
    entry_limit_team: int = 500000

    # Storage
    r2_bucket: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_endpoint: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # CORS
    cors_origins: list[str] | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            database_url=os.getenv("DATABASE_URL", "postgresql://localhost:5432/pruv"),
            database_pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            jwt_secret=os.getenv("JWT_SECRET") or secrets.token_hex(32),
            github_client_id=os.getenv("GITHUB_CLIENT_ID", ""),
            github_client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
            r2_bucket=os.getenv("R2_BUCKET", ""),
            r2_access_key=os.getenv("R2_ACCESS_KEY", ""),
            r2_secret_key=os.getenv("R2_SECRET_KEY", ""),
            r2_endpoint=os.getenv("R2_ENDPOINT", ""),
        )


settings = Settings.from_env()

# Warn if JWT_SECRET is auto-generated (ephemeral — tokens invalidate on restart)
if not os.getenv("JWT_SECRET"):
    warnings.warn(
        "JWT_SECRET not set. Using auto-generated key. "
        "All tokens will be invalidated on server restart. "
        "Set JWT_SECRET in your environment for production.",
        stacklevel=1,
    )
