"""Chain service — business logic for chain CRUD, verification, and sharing."""

from __future__ import annotations

import time
import uuid
from typing import Any

from xycore import XYEntry, hash_state, verify_chain
from xycore.redact import redact_state


class ChainService:
    """In-memory chain service. Replace with database-backed in production."""

    def __init__(self) -> None:
        self._chains: dict[str, dict[str, Any]] = {}
        self._entries: dict[str, list[dict[str, Any]]] = {}
        self._share_map: dict[str, str] = {}  # share_id -> chain_id

    def create_chain(
        self, user_id: str, name: str, description: str | None = None,
        tags: list[str] | None = None, auto_redact: bool = True,
    ) -> dict[str, Any]:
        chain_id = uuid.uuid4().hex[:12]
        chain = {
            "id": chain_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "tags": tags or [],
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

    def update_chain(self, chain_id: str, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        chain = self.get_chain(chain_id, user_id)
        if not chain:
            return None
        for key, value in updates.items():
            if key in ("name", "description", "tags", "auto_redact"):
                chain[key] = value
        chain["updated_at"] = time.time()
        return chain

    def delete_chain(self, chain_id: str, user_id: str) -> bool:
        chain = self.get_chain(chain_id, user_id)
        if not chain:
            return False
        del self._chains[chain_id]
        self._entries.pop(chain_id, None)
        share_id = chain.get("share_id")
        if share_id:
            self._share_map.pop(share_id, None)
        return True

    def get_entry_by_index(self, chain_id: str, index: int) -> dict[str, Any] | None:
        entries = self._entries.get(chain_id, [])
        if 0 <= index < len(entries):
            return entries[index]
        return None

    def undo_last_entry(self, chain_id: str, user_id: str) -> dict[str, Any] | None:
        chain = self.get_chain(chain_id, user_id)
        if not chain:
            return None
        entries = self._entries.get(chain_id, [])
        if not entries:
            return None
        removed = entries.pop()
        chain["length"] = len(entries)
        if entries:
            chain["head_xy"] = entries[-1]["xy"]
            chain["head_y"] = entries[-1]["y"]
        else:
            chain["head_xy"] = None
            chain["head_y"] = "GENESIS"
            chain["root_xy"] = None
        chain["updated_at"] = time.time()
        return removed

    def get_chain_count(self, user_id: str) -> int:
        return len([c for c in self._chains.values() if c["user_id"] == user_id])

    def get_entry_count(self, user_id: str) -> int:
        total = 0
        for chain in self._chains.values():
            if chain["user_id"] == user_id:
                total += chain.get("length", 0)
        return total

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

    def verify_payments(self, chain_id: str) -> dict[str, Any]:
        """Verify all payment entries in a chain.

        Walks the chain, finds entries with xy_proof data,
        recomputes each BalanceProof, and verifies hashes match.
        """
        from xycore.balance import BalanceProof

        entries_data = self._entries.get(chain_id, [])

        payment_count = 0
        verified_count = 0
        breaks: list[int] = []
        balances: dict[str, float] = {}
        total_volume = 0.0

        for i, entry in enumerate(entries_data):
            # xy_proof can be in metadata directly, or nested under
            # metadata.data (when created via Agent -> PruvClient)
            meta = entry.get("metadata", {})
            xy_data = meta.get("xy_proof")
            if xy_data is None:
                nested = meta.get("data", {})
                if isinstance(nested, dict):
                    xy_data = nested.get("xy_proof")
            if xy_data is None:
                continue

            payment_count += 1

            try:
                valid = BalanceProof.verify_proof(xy_data)
                if valid:
                    verified_count += 1
                    for party, bal in xy_data.get("after", {}).items():
                        balances[party] = bal
                    total_volume += xy_data.get("amount", 0)
                else:
                    breaks.append(i)
            except Exception:
                breaks.append(i)

        all_valid = len(breaks) == 0 and payment_count > 0

        if payment_count == 0:
            message = "No payment entries found"
        elif all_valid:
            message = f"✓ {verified_count}/{payment_count} payments verified"
        else:
            message = f"✗ {len(breaks)} payment(s) failed verification"

        return {
            "chain_id": chain_id,
            "payment_count": payment_count,
            "verified_count": verified_count,
            "breaks": breaks,
            "all_valid": all_valid,
            "final_balances": balances,
            "total_volume": total_volume,
            "message": message,
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
