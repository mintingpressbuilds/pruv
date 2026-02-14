"""XYEntry — the fundamental unit of the XY chain."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .crypto import compute_xy


@dataclass
class XYEntry:
    """A single entry in an XY chain.

    Captures a state transformation: X (before) -> Y (after) with
    cryptographic proof XY that the transformation occurred.
    """

    # Identity
    index: int
    timestamp: float
    operation: str

    # The XY core
    x: str  # Hash of state before
    y: str  # Hash of state after
    xy: str  # Proof hash (xy_...)

    # Optional: actual states for inspection
    x_state: dict | None = None
    y_state: dict | None = None

    # Metadata
    status: str = "success"  # success, failed, pending
    verified: bool = True
    metadata: dict = field(default_factory=dict)

    # Digital signature (optional)
    signature: str | None = None
    signer_id: str | None = None
    public_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry to a dictionary."""
        d: dict[str, Any] = {
            "index": self.index,
            "timestamp": self.timestamp,
            "operation": self.operation,
            "x": self.x,
            "y": self.y,
            "xy": self.xy,
            "status": self.status,
            "verified": self.verified,
            "metadata": self.metadata,
        }
        if self.x_state is not None:
            d["x_state"] = self.x_state
        if self.y_state is not None:
            d["y_state"] = self.y_state
        if self.signature is not None:
            d["signature"] = self.signature
        if self.signer_id is not None:
            d["signer_id"] = self.signer_id
        if self.public_key is not None:
            d["public_key"] = self.public_key
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "XYEntry":
        """Deserialize entry from a dictionary."""
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            operation=data["operation"],
            x=data["x"],
            y=data["y"],
            xy=data["xy"],
            x_state=data.get("x_state"),
            y_state=data.get("y_state"),
            status=data.get("status", "success"),
            verified=data.get("verified", True),
            metadata=data.get("metadata", {}),
            signature=data.get("signature"),
            signer_id=data.get("signer_id"),
            public_key=data.get("public_key"),
        )

    @classmethod
    def create(
        cls,
        index: int,
        operation: str,
        x: str,
        y: str,
        x_state: dict | None = None,
        y_state: dict | None = None,
        status: str = "success",
        metadata: dict | None = None,
        timestamp: float | None = None,
    ) -> "XYEntry":
        """Create a new entry, computing the XY proof hash automatically."""
        ts = timestamp if timestamp is not None else time.time()
        xy = compute_xy(x, operation, y, ts)
        return cls(
            index=index,
            timestamp=ts,
            operation=operation,
            x=x,
            y=y,
            xy=xy,
            x_state=x_state,
            y_state=y_state,
            status=status,
            verified=True,
            metadata=metadata or {},
        )
