"""Action observers for the wrapper system."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from xycore import XYChain


@dataclass
class Action:
    """Represents an observed action during wrapped execution."""

    operation: str
    timestamp: float
    args: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    status: str = "success"
    error: str | None = None
    duration: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "operation": self.operation,
            "timestamp": self.timestamp,
            "status": self.status,
            "duration": self.duration,
        }
        if self.args:
            d["args"] = self.args
        if self.error:
            d["error"] = self.error
        return d


class ActionObserver:
    """Observes and records actions during wrapped execution.

    Can be attached to a WrappedAgent to capture intermediate
    actions between the start and completion entries.
    """

    def __init__(self, chain: XYChain) -> None:
        self.chain = chain
        self.actions: list[Action] = []
        self._hooks: dict[str, list[Callable]] = {}

    def observe(
        self,
        operation: str,
        args: dict[str, Any] | None = None,
        result: Any = None,
        status: str = "success",
        error: str | None = None,
    ) -> Action:
        """Record an action and append it to the chain."""
        action = Action(
            operation=operation,
            timestamp=time.time(),
            args=args or {},
            result=result,
            status=status,
            error=error,
        )
        self.actions.append(action)

        # Append to chain
        y_state = action.to_dict()
        if result is not None and isinstance(result, (dict, str, int, float, bool)):
            y_state["result"] = result

        self.chain.append(
            operation=operation,
            y_state=y_state,
            status=status,
            metadata={"observer": True},
        )

        # Call hooks
        for hook in self._hooks.get(operation, []):
            try:
                hook(action)
            except Exception:
                pass
        for hook in self._hooks.get("*", []):
            try:
                hook(action)
            except Exception:
                pass

        return action

    def on(self, operation: str, callback: Callable) -> None:
        """Register a hook for a specific operation type."""
        if operation not in self._hooks:
            self._hooks[operation] = []
        self._hooks[operation].append(callback)

    def get_actions(self, operation: str | None = None) -> list[Action]:
        """Get recorded actions, optionally filtered by operation."""
        if operation is None:
            return list(self.actions)
        return [a for a in self.actions if a.operation == operation]

    @property
    def count(self) -> int:
        return len(self.actions)

    @property
    def failed_actions(self) -> list[Action]:
        return [a for a in self.actions if a.status == "failed"]

    def summary(self) -> dict[str, Any]:
        """Get a summary of all observed actions."""
        ops: dict[str, int] = {}
        for a in self.actions:
            ops[a.operation] = ops.get(a.operation, 0) + 1
        return {
            "total_actions": len(self.actions),
            "operations": ops,
            "failed": len(self.failed_actions),
            "duration": (
                self.actions[-1].timestamp - self.actions[0].timestamp
                if len(self.actions) > 1
                else 0
            ),
        }


class FileObserver(ActionObserver):
    """Specialized observer for file system operations."""

    def __init__(self, chain: XYChain) -> None:
        super().__init__(chain)
        self.files_read: list[str] = []
        self.files_written: list[str] = []
        self.files_deleted: list[str] = []

    def file_read(self, path: str, size: int = 0) -> Action:
        self.files_read.append(path)
        return self.observe("file.read", {"path": path, "size": size})

    def file_write(self, path: str, size: int = 0) -> Action:
        self.files_written.append(path)
        return self.observe("file.write", {"path": path, "size": size})

    def file_delete(self, path: str) -> Action:
        self.files_deleted.append(path)
        return self.observe("file.delete", {"path": path})

    def summary(self) -> dict[str, Any]:
        base = super().summary()
        base["files_read"] = len(self.files_read)
        base["files_written"] = len(self.files_written)
        base["files_deleted"] = len(self.files_deleted)
        return base


class APIObserver(ActionObserver):
    """Specialized observer for API calls."""

    def __init__(self, chain: XYChain) -> None:
        super().__init__(chain)
        self.requests: list[dict[str, Any]] = []

    def api_call(
        self,
        method: str,
        url: str,
        status_code: int = 200,
        duration: float = 0.0,
    ) -> Action:
        req = {"method": method, "url": url, "status_code": status_code}
        self.requests.append(req)
        status = "success" if status_code < 400 else "failed"
        return self.observe(
            f"api.{method.lower()}",
            {"url": url, "status_code": status_code},
            status=status,
        )

    def summary(self) -> dict[str, Any]:
        base = super().summary()
        base["total_requests"] = len(self.requests)
        base["failed_requests"] = sum(
            1 for r in self.requests if r["status_code"] >= 400
        )
        return base
