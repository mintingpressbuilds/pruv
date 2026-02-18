"""FastAPI dependencies for auth, rate limiting, and database."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, Header, HTTPException, Request

from .rate_limit import rate_limiter, RateLimitResult
from .security import (
    decode_jwt_token,
    extract_bearer_token,
    verify_api_key_format,
)

logger = logging.getLogger("pruv.api.dependencies")


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Extract and verify the current user from auth header.

    For API keys: look up in database. Auto-provision on first use.
    For JWT tokens: decode and verify signature.
    """
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization")

    # Check if it's an API key (pv_live_ or pv_test_ prefix)
    if verify_api_key_format(token):
        from ..services.auth_service import auth_service

        # Look up in database
        user = auth_service.get_user_by_api_key(token)
        if user:
            return user

        # Auto-provision: create user + key record on first use
        try:
            return auth_service.auto_provision_api_key(token)
        except Exception:
            logger.exception("Failed to auto-provision API key")
            raise HTTPException(status_code=401, detail="Invalid API key")

    # Try JWT
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload["sub"]

    # Ensure JWT user exists in database
    try:
        from ..services.auth_service import auth_service
        auth_service.ensure_user(user_id)
    except Exception:
        pass  # Non-fatal — user may already exist

    return {
        "id": user_id,
        "type": "jwt",
        "plan": payload.get("plan", "free"),
        "scopes": payload.get("scopes", ["read", "write"]),
    }


async def check_rate_limit(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> RateLimitResult:
    """Check rate limit for the current user.

    Stores rate limit headers on request state for middleware injection.
    """
    key = f"rate:{user['id']}"
    result = rate_limiter.check(key, plan=user.get("plan", "free"))

    # Store headers so middleware can inject them into the response
    request.state.rate_limit_headers = result.to_headers()

    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=result.to_headers(),
        )
    return result


async def optional_user(authorization: str | None = Header(None)) -> dict[str, Any] | None:
    """Extract the current user if auth is present, otherwise return None."""
    if not authorization:
        return None
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def require_scope(scope: str):
    """Create a dependency that requires a specific scope."""
    async def _check(user: dict[str, Any] = Depends(get_current_user)):
        if scope not in user.get("scopes", []):
            raise HTTPException(status_code=403, detail=f"Missing scope: {scope}")
        return user
    return _check


# Pre-built scope dependencies
require_read = require_scope("read")
require_write = require_scope("write")
require_admin = require_scope("admin")
