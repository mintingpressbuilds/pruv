"""Agent — wrap any AI agent with automatic action verification.

Every action is hashed, chained, and stored as a pruv receipt.

Usage:
    from pruv import Agent

    agent = Agent("email-assistant", api_key="pv_live_xxx")
    agent.action("read_email", {"from": "boss@co.com"})
    agent.action("send_reply", {"to": "boss@co.com", "body": "done"})
    chain = agent.chain()  # full verified history
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from pruv.client import PruvClient


class Agent:
    """Wraps any AI agent with automatic action verification.

    Every call to ``action()`` appends an entry to a pruv chain on the
    server.  The chain is cryptographically linked — tamper with one
    entry and the chain breaks.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.client = PruvClient(api_key=api_key, endpoint=endpoint)
        self.metadata = metadata or {}
        self._chain: dict[str, Any] | None = None
        self._action_count = 0
        self._init_chain()

    def _init_chain(self) -> None:
        """Create a new pruv chain for this agent session."""
        self._chain = self.client.create_chain(
            name=f"{self.name}-{int(time.time())}",
            metadata={
                "agent": self.name,
                "started_at": time.time(),
                **self.metadata,
            },
        )

    def action(
        self,
        action_type: str,
        data: dict[str, Any],
        sensitive_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record a verified action.

        Args:
            action_type: What the agent did (``"read_email"``, ``"send_message"``, etc.)
            data: Action payload (parameters, results, context).
            sensitive_keys: Keys in *data* to hash instead of storing raw.
                Values are replaced with their SHA-256 digest so you can
                verify without exposing content.

        Returns:
            Receipt dict with hash, chain position, and timestamp.
        """
        self._action_count += 1

        safe_data = self._redact(data, sensitive_keys or [])

        entry_data = {
            "action": action_type,
            "seq": self._action_count,
            "ts": time.time(),
            "data": safe_data,
        }

        assert self._chain is not None  # noqa: S101
        return self.client.add_entry(
            chain_id=self._chain["id"],
            data=entry_data,
        )

    def verify(self) -> dict[str, Any]:
        """Verify the entire action chain.

        Returns verification result with status and any broken links.
        """
        assert self._chain is not None  # noqa: S101
        return self.client.verify_chain(self._chain["id"])

    def chain(self) -> dict[str, Any]:
        """Get the full chain with all entries."""
        assert self._chain is not None  # noqa: S101
        return self.client.get_chain(self._chain["id"])

    def receipt(self, entry_id: str) -> dict[str, Any]:
        """Get a single action receipt by ID."""
        assert self._chain is not None  # noqa: S101
        return self.client.get_entry(self._chain["id"], entry_id)

    def export(self) -> str:
        """Export the chain as a self-verifying HTML artifact."""
        assert self._chain is not None  # noqa: S101
        return self.client.export_chain(self._chain["id"])

    # ------------------------------------------------------------------
    # Redaction
    # ------------------------------------------------------------------

    def _redact(
        self, data: dict[str, Any], sensitive_keys: list[str],
    ) -> dict[str, Any]:
        """Replace sensitive values with their SHA-256 hash."""
        if not sensitive_keys:
            return data

        redacted: dict[str, Any] = {}
        for k, v in data.items():
            if k in sensitive_keys:
                raw = json.dumps(v, sort_keys=True) if not isinstance(v, str) else v
                redacted[k] = {
                    "_redacted": True,
                    "_hash": hashlib.sha256(raw.encode()).hexdigest(),
                }
            else:
                redacted[k] = v
        return redacted


class ActionError(Exception):
    """Raised when an action fails verification."""
