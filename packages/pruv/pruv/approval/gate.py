"""Approval gate — webhook-based human approval for high-risk operations."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApprovalRequest:
    """Request sent to the approval webhook."""

    chain_id: str
    entry_index: int
    operation: str
    x_state: dict[str, Any] | None = None
    proposed_y_state: dict[str, Any] | None = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "entry_index": self.entry_index,
            "operation": self.operation,
            "x_state": self.x_state,
            "proposed_y_state": self.proposed_y_state,
            "timestamp": self.timestamp,
        }


@dataclass
class ApprovalResponse:
    """Response from the approval webhook."""

    status: str  # approved, denied, timeout
    approved_by: str | None = None
    reason: str | None = None

    @property
    def is_approved(self) -> bool:
        return self.status == "approved"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"status": self.status}
        if self.approved_by:
            d["approved_by"] = self.approved_by
        if self.reason:
            d["reason"] = self.reason
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalResponse":
        return cls(
            status=data["status"],
            approved_by=data.get("approved_by"),
            reason=data.get("reason"),
        )


class ApprovalGate:
    """Human approval gate via webhook for high-risk operations."""

    def __init__(
        self,
        webhook_url: str,
        timeout: int = 300,
        operations: set[str] | None = None,
        on_timeout: str = "deny",
    ) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.operations = operations or {"file.write", "deploy", "database.migrate"}
        self.on_timeout = on_timeout

    def requires_approval(self, operation: str) -> bool:
        """Check if an operation requires approval."""
        return operation in self.operations

    async def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """Send an approval request to the webhook."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.webhook_url, json=request.to_dict())
                if resp.status_code == 200:
                    return ApprovalResponse.from_dict(resp.json())
                return ApprovalResponse(status="denied", reason=f"HTTP {resp.status_code}")
        except Exception as e:
            if self.on_timeout == "approve":
                return ApprovalResponse(status="approved", reason="timeout-auto-approved")
            return ApprovalResponse(status="timeout", reason=str(e))

    async def gate(
        self,
        chain_id: str,
        entry_index: int,
        operation: str,
        x_state: dict[str, Any] | None = None,
        proposed_y_state: dict[str, Any] | None = None,
    ) -> ApprovalResponse:
        """Full gate check — only calls webhook if operation requires approval."""
        if not self.requires_approval(operation):
            return ApprovalResponse(status="approved", reason="no-approval-required")

        request = ApprovalRequest(
            chain_id=chain_id,
            entry_index=entry_index,
            operation=operation,
            x_state=x_state,
            proposed_y_state=proposed_y_state,
        )
        return await self.request_approval(request)
