"""FastAPI dependencies for auth, rate limiting, and database."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, Header, HTTPException, Request

from .rate_limit import rate_limiter, RateLimitResult
from .security import (
    decode_jwt_token,
    extract_bearer_token,
    hash_api_key,
    verify_api_key_format,
)


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Extract and verify the current user from auth header."""
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization")

    # Check if it's an API key
    if verify_api_key_format(token):
        key_hash = hash_api_key(token)
        # In production, look up key_hash in database
        return {
            "id": f"apikey_{key_hash[:12]}",
            "type": "api_key",
            "key_hash": key_hash,
            "plan": "free",
            "scopes": ["read", "write"],
        }

    # Try JWT
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "id": payload["sub"],
        "type": "jwt",
        "plan": payload.get("plan", "free"),
        "scopes": payload.get("scopes", ["read"]),
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
