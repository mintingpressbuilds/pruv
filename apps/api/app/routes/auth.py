"""Authentication routes — API keys, OAuth, user management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..core.config import settings
from ..core.dependencies import check_rate_limit, get_current_user, require_write
from ..core.rate_limit import RateLimitResult, rate_limiter
from ..core.security import create_jwt_token
from ..schemas.schemas import ApiKeyCreate, ApiKeyCreatedResponse
from ..services.auth_service import auth_service

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    body: ApiKeyCreate,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Create a new API key. The full key is only returned once."""
    result = auth_service.create_api_key(
        user_id=user["id"],
        name=body.name,
        scopes=body.scopes,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create API key")
    return result


@router.get("/api-keys")
async def list_api_keys(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """List all API keys for the current user."""
    keys = auth_service.list_api_keys(user["id"])
    return {"keys": keys}


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Revoke an API key."""
    success = auth_service.revoke_api_key(key_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"revoked": True}


@router.get("/me")
async def get_current_user_info(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get current user information."""
    return {
        "id": user["id"],
        "type": user["type"],
        "plan": user.get("plan", "free"),
        "scopes": user.get("scopes", []),
    }


@router.get("/usage")
async def get_usage(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get usage information for the current user."""
    return auth_service.get_usage(user["id"])


# ──── OAuth Callbacks ────


@router.post("/oauth/github")
async def github_oauth_callback(
    code: str = Query(..., min_length=8, max_length=256),
    request: Request = None,
):
    """Handle GitHub OAuth callback."""
    # Rate limit OAuth callbacks to prevent brute force
    client_ip = request.client.host if request.client else "unknown"
    rl = rate_limiter.check(f"oauth:{client_ip}", plan="free")
    if not rl.allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rl.to_headers())
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")
    # In production: exchange code for token via GitHub API, fetch user info
    user = auth_service.get_or_create_oauth_user(
        provider="github",
        provider_id=f"gh_{code[:8]}",
        email=f"{code[:8]}@github.com",
        name=f"GitHub User {code[:8]}",
    )
    token = create_jwt_token(user["id"])
    return {"token": token, "user": user}


@router.post("/oauth/google")
async def google_oauth_callback(
    code: str = Query(..., min_length=8, max_length=256),
    request: Request = None,
):
    """Handle Google OAuth callback."""
    # Rate limit OAuth callbacks to prevent brute force
    client_ip = request.client.host if request.client else "unknown"
    rl = rate_limiter.check(f"oauth:{client_ip}", plan="free")
    if not rl.allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rl.to_headers())
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    # In production: exchange code for token via Google API, fetch user info
    user = auth_service.get_or_create_oauth_user(
        provider="google",
        provider_id=f"g_{code[:8]}",
        email=f"{code[:8]}@gmail.com",
        name=f"Google User {code[:8]}",
    )
    token = create_jwt_token(user["id"])
    return {"token": token, "user": user}
