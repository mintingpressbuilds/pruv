"""Webhook management routes."""

from __future__ import annotations

import ipaddress
import secrets
import time
import uuid
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.dependencies import check_rate_limit, get_current_user, require_write
from ..core.rate_limit import RateLimitResult

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])

# In-memory webhook storage
_webhooks: dict[str, dict[str, Any]] = {}

VALID_EVENTS = [
    "chain.created",
    "chain.deleted",
    "entry.appended",
    "entry.batch_appended",
    "checkpoint.created",
    "checkpoint.restored",
    "receipt.created",
    "verification.completed",
    "verification.failed",
    "alert.triggered",
]

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]"}


def _validate_webhook_url(url: str) -> None:
    """Validate a webhook URL to prevent SSRF."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise HTTPException(status_code=400, detail="Webhook URL must use HTTPS")
    hostname = parsed.hostname or ""
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid webhook URL")
    if hostname in _BLOCKED_HOSTS:
        raise HTTPException(status_code=400, detail="Webhook URL cannot target localhost")
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            raise HTTPException(status_code=400, detail="Webhook URL cannot target private addresses")
    except ValueError:
        pass  # Not an IP, it's a hostname — that's fine


def _validate_events(events: list[str]) -> None:
    """Validate webhook event types."""
    invalid = [e for e in events if e not in VALID_EVENTS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid event types: {', '.join(invalid)}")


class WebhookCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    events: list[str] = Field(default=["chain.created", "entry.appended"])


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    secret: str | None = None
    active: bool = True
    created_at: float | None = None

    model_config = {"from_attributes": True}


class WebhookUpdate(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    events: list[str] | None = None
    active: bool | None = None


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    body: WebhookCreate,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Create a webhook endpoint."""
    _validate_webhook_url(body.url)
    _validate_events(body.events)

    webhook_id = uuid.uuid4().hex[:12]
    secret = secrets.token_hex(32)
    webhook = {
        "id": webhook_id,
        "user_id": user["id"],
        "url": body.url,
        "events": body.events,
        "secret": secret,
        "active": True,
        "created_at": time.time(),
    }
    _webhooks[webhook_id] = webhook
    return webhook


@router.get("")
async def list_webhooks(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """List all webhooks for the current user."""
    hooks = [
        {k: v for k, v in wh.items() if k != "user_id"}
        for wh in _webhooks.values()
        if wh["user_id"] == user["id"]
    ]
    return {"webhooks": hooks}


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get a webhook by ID."""
    wh = _webhooks.get(webhook_id)
    if not wh or wh["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return wh


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    body: WebhookUpdate,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Update a webhook."""
    wh = _webhooks.get(webhook_id)
    if not wh or wh["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if body.url is not None:
        _validate_webhook_url(body.url)
        wh["url"] = body.url
    if body.events is not None:
        _validate_events(body.events)
        wh["events"] = body.events
    if body.active is not None:
        wh["active"] = body.active

    return wh


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Delete a webhook."""
    wh = _webhooks.get(webhook_id)
    if not wh or wh["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")
    del _webhooks[webhook_id]
    return {"deleted": True}


@router.get("/events/list")
async def list_webhook_events():
    """List all available webhook event types."""
    return {"events": VALID_EVENTS}
