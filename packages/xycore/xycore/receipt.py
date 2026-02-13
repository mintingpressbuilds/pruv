"""XYReceipt — summary of a completed chain of operations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ThinkingPhase:
    """Represents an AI agent's thinking/reasoning phase."""

    prompt: str
    reasoning: str | None = None
    plan: list[str] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "reasoning": self.reasoning,
            "plan": self.plan,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThinkingPhase":
        return cls(
            prompt=data["prompt"],
            reasoning=data.get("reasoning"),
            plan=data.get("plan", []),
            duration=data.get("duration", 0.0),
        )


@dataclass
class XYReceipt:
    """A receipt summarizing a chain of XY operations."""

    id: str
    task: str
    started: float
    completed: float
    duration: float

    chain_id: str
    entry_count: int

    first_x: str
    final_y: str
    root_xy: str
    head_xy: str

    all_verified: bool
    all_signatures_valid: bool = True

    agent_type: str | None = None
    thinking: ThinkingPhase | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def hash(self) -> str:
        """Compute a deterministic hash of this receipt."""
        data = {
            "id": self.id,
            "task": self.task,
            "chain_id": self.chain_id,
            "entry_count": self.entry_count,
            "first_x": self.first_x,
            "final_y": self.final_y,
            "root_xy": self.root_xy,
            "head_xy": self.head_xy,
            "all_verified": self.all_verified,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "task": self.task,
            "started": self.started,
            "completed": self.completed,
            "duration": self.duration,
            "chain_id": self.chain_id,
            "entry_count": self.entry_count,
            "first_x": self.first_x,
            "final_y": self.final_y,
            "root_xy": self.root_xy,
            "head_xy": self.head_xy,
            "all_verified": self.all_verified,
            "all_signatures_valid": self.all_signatures_valid,
            "hash": self.hash,
            "metadata": self.metadata,
        }
        if self.agent_type is not None:
            d["agent_type"] = self.agent_type
        if self.thinking is not None:
            d["thinking"] = self.thinking.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "XYReceipt":
        thinking = None
        if "thinking" in data:
            thinking = ThinkingPhase.from_dict(data["thinking"])
        return cls(
            id=data["id"],
            task=data["task"],
            started=data["started"],
            completed=data["completed"],
            duration=data["duration"],
            chain_id=data["chain_id"],
            entry_count=data["entry_count"],
            first_x=data["first_x"],
            final_y=data["final_y"],
            root_xy=data["root_xy"],
            head_xy=data["head_xy"],
            all_verified=data["all_verified"],
            all_signatures_valid=data.get("all_signatures_valid", True),
            agent_type=data.get("agent_type"),
            thinking=thinking,
            metadata=data.get("metadata", {}),
        )
