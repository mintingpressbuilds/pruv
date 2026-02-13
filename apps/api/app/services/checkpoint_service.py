"""Checkpoint service — create, list, preview, and restore checkpoints."""

from __future__ import annotations

import time
import uuid
from typing import Any

from .chain_service import chain_service


class CheckpointService:
    """In-memory checkpoint service."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, list[dict[str, Any]]] = {}  # chain_id -> [checkpoints]

    def create_checkpoint(
        self, chain_id: str, user_id: str, name: str,
    ) -> dict[str, Any] | None:
        chain = chain_service.get_chain(chain_id, user_id)
        if not chain:
            return None

        entries = chain_service.list_entries(chain_id)
        checkpoint = {
            "id": uuid.uuid4().hex[:12],
            "chain_id": chain_id,
            "name": name,
            "entry_index": chain["length"] - 1 if chain["length"] > 0 else -1,
            "snapshot": {
                "chain": dict(chain),
                "entries": list(entries),
            },
            "created_at": time.time(),
        }

        if chain_id not in self._checkpoints:
            self._checkpoints[chain_id] = []
        self._checkpoints[chain_id].append(checkpoint)
        return checkpoint

    def list_checkpoints(self, chain_id: str) -> list[dict[str, Any]]:
        return [
            {
                "id": cp["id"],
                "chain_id": cp["chain_id"],
                "name": cp["name"],
                "entry_index": cp["entry_index"],
                "created_at": cp["created_at"],
            }
            for cp in self._checkpoints.get(chain_id, [])
        ]

    def preview_restore(
        self, chain_id: str, checkpoint_id: str, user_id: str,
    ) -> dict[str, Any] | None:
        chain = chain_service.get_chain(chain_id, user_id)
        if not chain:
            return None

        cp = self._find_checkpoint(chain_id, checkpoint_id)
        if not cp:
            return None

        current_index = chain["length"] - 1 if chain["length"] > 0 else -1
        return {
            "checkpoint_id": cp["id"],
            "checkpoint_name": cp["name"],
            "current_entry_index": current_index,
            "target_entry_index": cp["entry_index"],
            "entries_to_rollback": max(0, current_index - cp["entry_index"]),
        }

    def restore_checkpoint(
        self, chain_id: str, checkpoint_id: str, user_id: str,
    ) -> dict[str, Any] | None:
        chain = chain_service.get_chain(chain_id, user_id)
        if not chain:
            return None

        cp = self._find_checkpoint(chain_id, checkpoint_id)
        if not cp:
            return None

        snapshot = cp["snapshot"]

        # Restore chain metadata
        for key in ["length", "root_xy", "head_xy", "head_y"]:
            chain[key] = snapshot["chain"][key]
        chain["updated_at"] = time.time()

        # Restore entries
        chain_service._entries[chain_id] = list(snapshot["entries"])

        return {
            "restored": True,
            "checkpoint_id": checkpoint_id,
            "new_length": chain["length"],
        }

    def _find_checkpoint(self, chain_id: str, checkpoint_id: str) -> dict[str, Any] | None:
        for cp in self._checkpoints.get(chain_id, []):
            if cp["id"] == checkpoint_id:
                return cp
        return None


# Global instance
checkpoint_service = CheckpointService()
