"""Webhook delivery service for the pruv API."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WebhookEvent(str, Enum):
    """Supported webhook event types."""
    CHAIN_CREATED = "chain.created"
    CHAIN_UPDATED = "chain.updated"
    CHAIN_DELETED = "chain.deleted"
    ENTRY_APPENDED = "entry.appended"
    ENTRY_BATCH = "entry.batch"
    VERIFICATION_PASSED = "verification.passed"
    VERIFICATION_FAILED = "verification.failed"
    CHECKPOINT_CREATED = "checkpoint.created"
    CHECKPOINT_RESTORED = "checkpoint.restored"
    RECEIPT_GENERATED = "receipt.generated"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    USAGE_THRESHOLD = "usage.threshold"


@dataclass
class WebhookEndpoint:
    """A registered webhook endpoint."""
    id: str
    user_id: str
    url: str
    events: list[str]
    secret: str
    active: bool = True
    created_at: float = field(default_factory=time.time)
    last_delivery: float = 0.0
    failure_count: int = 0
    max_failures: int = 10

    @property
    def is_disabled(self) -> bool:
        """Check if webhook has been auto-disabled due to failures."""
        return self.failure_count >= self.max_failures

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "events": self.events,
            "active": self.active and not self.is_disabled,
            "created_at": self.created_at,
            "last_delivery": self.last_delivery,
            "failure_count": self.failure_count,
        }


@dataclass
class WebhookDelivery:
    """A webhook delivery attempt."""
    id: str
    endpoint_id: str
    event: str
    payload: dict[str, Any]
    status: str = "pending"  # pending, delivered, failed
    response_code: int | None = None
    response_body: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: float = field(default_factory=time.time)
    delivered_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "event": self.event,
            "status": self.status,
            "response_code": self.response_code,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
        }


def compute_webhook_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload.

    The signature is sent in the X-Pruv-Signature header.
    Receivers should compute the same signature and compare
    to verify the payload was sent by pruv.
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def build_webhook_payload(
    event: str,
    data: dict[str, Any],
    timestamp: float | None = None,
) -> dict[str, Any]:
    """Build a standardized webhook payload."""
    return {
        "id": f"evt_{uuid.uuid4().hex[:24]}",
        "event": event,
        "created_at": timestamp or time.time(),
        "data": data,
        "api_version": "2026-02-01",
    }


class WebhookService:
    """Service for managing and delivering webhooks."""

    def __init__(self) -> None:
        self._endpoints: dict[str, WebhookEndpoint] = {}
        self._deliveries: list[WebhookDelivery] = []

    def register_endpoint(
        self,
        user_id: str,
        url: str,
        events: list[str],
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint."""
        endpoint = WebhookEndpoint(
            id=f"whk_{uuid.uuid4().hex[:24]}",
            user_id=user_id,
            url=url,
            events=events,
            secret=f"whsec_{uuid.uuid4().hex}",
        )
        self._endpoints[endpoint.id] = endpoint
        return endpoint

    def get_endpoint(self, endpoint_id: str) -> WebhookEndpoint | None:
        """Get a webhook endpoint by ID."""
        return self._endpoints.get(endpoint_id)

    def list_endpoints(self, user_id: str) -> list[WebhookEndpoint]:
        """List all webhook endpoints for a user."""
        return [
            ep for ep in self._endpoints.values()
            if ep.user_id == user_id
        ]

    def update_endpoint(
        self,
        endpoint_id: str,
        url: str | None = None,
        events: list[str] | None = None,
        active: bool | None = None,
    ) -> WebhookEndpoint | None:
        """Update a webhook endpoint."""
        endpoint = self._endpoints.get(endpoint_id)
        if not endpoint:
            return None

        if url is not None:
            endpoint.url = url
        if events is not None:
            endpoint.events = events
        if active is not None:
            endpoint.active = active
            if active:
                endpoint.failure_count = 0

        return endpoint

    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete a webhook endpoint."""
        if endpoint_id in self._endpoints:
            del self._endpoints[endpoint_id]
            return True
        return False

    def rotate_secret(self, endpoint_id: str) -> str | None:
        """Rotate the signing secret for an endpoint."""
        endpoint = self._endpoints.get(endpoint_id)
        if not endpoint:
            return None
        endpoint.secret = f"whsec_{uuid.uuid4().hex}"
        return endpoint.secret

    def queue_delivery(
        self,
        event: str,
        data: dict[str, Any],
        user_id: str,
    ) -> list[WebhookDelivery]:
        """Queue webhook deliveries for all matching endpoints."""
        deliveries = []
        payload = build_webhook_payload(event, data)

        for endpoint in self._endpoints.values():
            if endpoint.user_id != user_id:
                continue
            if not endpoint.active or endpoint.is_disabled:
                continue
            if event not in endpoint.events and "*" not in endpoint.events:
                continue

            delivery = WebhookDelivery(
                id=f"dlv_{uuid.uuid4().hex[:24]}",
                endpoint_id=endpoint.id,
                event=event,
                payload=payload,
            )
            self._deliveries.append(delivery)
            deliveries.append(delivery)

        return deliveries

    def get_deliveries(
        self,
        endpoint_id: str,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        """Get recent deliveries for an endpoint."""
        deliveries = [
            d for d in self._deliveries
            if d.endpoint_id == endpoint_id
        ]
        return deliveries[-limit:]

    def mark_delivered(
        self,
        delivery_id: str,
        response_code: int,
        response_body: str = "",
    ) -> None:
        """Mark a delivery as successfully delivered."""
        for delivery in self._deliveries:
            if delivery.id == delivery_id:
                delivery.status = "delivered"
                delivery.response_code = response_code
                delivery.response_body = response_body[:1000]
                delivery.delivered_at = time.time()
                delivery.attempts += 1

                # Update endpoint stats
                endpoint = self._endpoints.get(delivery.endpoint_id)
                if endpoint:
                    endpoint.last_delivery = time.time()
                    endpoint.failure_count = 0
                break

    def mark_failed(
        self,
        delivery_id: str,
        response_code: int | None = None,
        error: str = "",
    ) -> None:
        """Mark a delivery as failed."""
        for delivery in self._deliveries:
            if delivery.id == delivery_id:
                delivery.attempts += 1
                delivery.response_code = response_code

                if delivery.attempts >= delivery.max_attempts:
                    delivery.status = "failed"
                    delivery.response_body = error[:1000]

                    # Increment endpoint failure count
                    endpoint = self._endpoints.get(delivery.endpoint_id)
                    if endpoint:
                        endpoint.failure_count += 1
                break

    def get_pending_deliveries(self) -> list[WebhookDelivery]:
        """Get all pending deliveries that need to be sent."""
        return [
            d for d in self._deliveries
            if d.status == "pending" and d.attempts < d.max_attempts
        ]

    def get_delivery_stats(self, user_id: str) -> dict[str, Any]:
        """Get webhook delivery statistics for a user."""
        user_endpoints = {
            ep.id for ep in self._endpoints.values()
            if ep.user_id == user_id
        }
        user_deliveries = [
            d for d in self._deliveries
            if d.endpoint_id in user_endpoints
        ]

        total = len(user_deliveries)
        delivered = sum(1 for d in user_deliveries if d.status == "delivered")
        failed = sum(1 for d in user_deliveries if d.status == "failed")
        pending = sum(1 for d in user_deliveries if d.status == "pending")

        return {
            "total_deliveries": total,
            "delivered": delivered,
            "failed": failed,
            "pending": pending,
            "success_rate": round(delivered / total, 4) if total > 0 else 0,
            "active_endpoints": len([
                ep for ep in self._endpoints.values()
                if ep.user_id == user_id and ep.active and not ep.is_disabled
            ]),
        }


# Global webhook service instance
_webhook_service: WebhookService | None = None


def get_webhook_service() -> WebhookService:
    """Get or create the global webhook service."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
