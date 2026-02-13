"""Chain service — business logic for chain CRUD, verification, and sharing."""

from __future__ import annotations

import time
import uuid
from typing import Any

from xycore import XYChain, XYEntry, hash_state, verify_chain, verify_entry
from xycore.redact import redact_state


class ChainService:
    """In-memory chain service. Replace with database-backed in production."""

    def __init__(self) -> None:
        self._chains: dict[str, dict[str, Any]] = {}
        self._entries: dict[str, list[dict[str, Any]]] = {}
        self._share_map: dict[str, str] = {}  # share_id -> chain_id

    def create_chain(self, user_id: str, name: str, auto_redact: bool = True) -> dict[str, Any]:
        chain_id = uuid.uuid4().hex[:12]
        chain = {
            "id": chain_id,
            "user_id": user_id,
            "name": name,
            "length": 0,
            "root_xy": None,
            "head_xy": None,
            "head_y": "GENESIS",
            "auto_redact": auto_redact,
            "share_id": None,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self._chains[chain_id] = chain
        self._entries[chain_id] = []
        return chain

    def get_chain(self, chain_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        chain = self._chains.get(chain_id)
        if chain and user_id and chain["user_id"] != user_id:
            return None
        return chain

    def list_chains(self, user_id: str) -> list[dict[str, Any]]:
        return [c for c in self._chains.values() if c["user_id"] == user_id]

    def append_entry(
        self,
        chain_id: str,
        user_id: str,
        operation: str,
        x_state: dict | None = None,
        y_state: dict | None = None,
        status: str = "success",
        metadata: dict | None = None,
        signature: str | None = None,
        signer_id: str | None = None,
        public_key: str | None = None,
    ) -> dict[str, Any] | None:
        chain = self.get_chain(chain_id, user_id)
        if not chain:
            return None

        entries = self._entries[chain_id]
        index = len(entries)

        # Auto-redact
        if chain.get("auto_redact", True):
            if x_state:
                x_state = redact_state(x_state)
            if y_state:
                y_state = redact_state(y_state)

        # Compute hashes
        x = chain["head_y"]
        if index == 0:
            x = "GENESIS"

        y = hash_state(y_state) if y_state else hash_state({})
        ts = time.time()

        from xycore.crypto import compute_xy
        xy = compute_xy(x, operation, y, ts)

        entry = {
            "id": uuid.uuid4().hex[:12],
            "chain_id": chain_id,
            "index": index,
            "timestamp": ts,
            "operation": operation,
            "x": x,
            "y": y,
            "xy": xy,
            "x_state": x_state,
            "y_state": y_state,
            "status": status,
            "verified": True,
            "metadata": metadata or {},
            "signature": signature,
            "signer_id": signer_id,
            "public_key": public_key,
        }

        entries.append(entry)

        # Update chain
        chain["length"] = len(entries)
        chain["head_xy"] = xy
        chain["head_y"] = y
        if index == 0:
            chain["root_xy"] = xy
        chain["updated_at"] = time.time()

        return entry

    def batch_append(
        self, chain_id: str, user_id: str, entries_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        results = []
        for data in entries_data:
            entry = self.append_entry(
                chain_id=chain_id,
                user_id=user_id,
                operation=data["operation"],
                x_state=data.get("x_state"),
                y_state=data.get("y_state"),
                status=data.get("status", "success"),
                metadata=data.get("metadata"),
                signature=data.get("signature"),
                signer_id=data.get("signer_id"),
                public_key=data.get("public_key"),
            )
            if entry:
                results.append(entry)
        return results

    def list_entries(self, chain_id: str, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        entries = self._entries.get(chain_id, [])
        return entries[offset : offset + limit]

    def verify_chain(self, chain_id: str) -> dict[str, Any]:
        entries_data = self._entries.get(chain_id, [])
        if not entries_data:
            return {"chain_id": chain_id, "valid": True, "length": 0, "break_index": None}

        xy_entries = []
        for e in entries_data:
            xy_entries.append(XYEntry(
                index=e["index"],
                timestamp=e["timestamp"],
                operation=e["operation"],
                x=e["x"],
                y=e["y"],
                xy=e["xy"],
                status=e.get("status", "success"),
            ))

        valid, break_index = verify_chain(xy_entries)
        return {
            "chain_id": chain_id,
            "valid": valid,
            "length": len(xy_entries),
            "break_index": break_index,
        }

    def create_share_link(self, chain_id: str, user_id: str) -> dict[str, Any] | None:
        chain = self.get_chain(chain_id, user_id)
        if not chain:
            return None
        if not chain.get("share_id"):
            chain["share_id"] = uuid.uuid4().hex[:12]
            self._share_map[chain["share_id"]] = chain_id
        return {
            "chain_id": chain_id,
            "share_id": chain["share_id"],
            "share_url": f"https://app.pruv.dev/shared/{chain['share_id']}",
        }

    def get_shared_chain(self, share_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
        chain_id = self._share_map.get(share_id)
        if not chain_id:
            # Search all chains
            for cid, chain in self._chains.items():
                if chain.get("share_id") == share_id:
                    chain_id = cid
                    self._share_map[share_id] = cid
                    break
        if not chain_id:
            return None
        chain = self._chains.get(chain_id)
        entries = self._entries.get(chain_id, [])
        if not chain:
            return None
        return chain, entries


# Global instance
chain_service = ChainService()
