"""Webhook management routes."""

from __future__ import annotations

import secrets
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.dependencies import get_current_user

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])

# In-memory webhook storage
_webhooks: dict[str, dict[str, Any]] = {}


class WebhookCreate(BaseModel):
    url: str
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
    url: str | None = None
    events: list[str] | None = None
    active: bool | None = None


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    body: WebhookCreate,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Create a webhook endpoint."""
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
    user: dict[str, Any] = Depends(get_current_user),
):
    """Update a webhook."""
    wh = _webhooks.get(webhook_id)
    if not wh or wh["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if body.url is not None:
        wh["url"] = body.url
    if body.events is not None:
        wh["events"] = body.events
    if body.active is not None:
        wh["active"] = body.active

    return wh


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Delete a webhook."""
    wh = _webhooks.get(webhook_id)
    if not wh or wh["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")
    del _webhooks[webhook_id]
    return {"deleted": True}


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
]


@router.get("/events/list")
async def list_webhook_events():
    """List all available webhook event types."""
    return {"events": VALID_EVENTS}
