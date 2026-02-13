"""Receipt service — create, retrieve, and export receipts."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from .chain_service import chain_service


class ReceiptService:
    """In-memory receipt service."""

    def __init__(self) -> None:
        self._receipts: dict[str, dict[str, Any]] = {}

    def create_receipt(
        self,
        chain_id: str,
        user_id: str,
        task: str,
        agent_type: str | None = None,
    ) -> dict[str, Any] | None:
        chain = chain_service.get_chain(chain_id, user_id)
        if not chain:
            return None

        entries = chain_service.list_entries(chain_id)
        verification = chain_service.verify_chain(chain_id)

        first_x = entries[0]["x"] if entries else "GENESIS"
        final_y = entries[-1]["y"] if entries else ""
        now = time.time()

        receipt_data = {
            "id": chain_id,
            "task": task,
            "chain_id": chain_id,
            "entry_count": len(entries),
            "first_x": first_x,
            "final_y": final_y,
            "root_xy": chain.get("root_xy", ""),
            "head_xy": chain.get("head_xy", ""),
            "all_verified": verification["valid"],
        }
        canonical = json.dumps(receipt_data, sort_keys=True, separators=(",", ":"))
        receipt_hash = hashlib.sha256(canonical.encode()).hexdigest()

        receipt_id = uuid.uuid4().hex[:12]
        receipt = {
            "id": receipt_id,
            "chain_id": chain_id,
            "task": task,
            "started": entries[0]["timestamp"] if entries else now,
            "completed": entries[-1]["timestamp"] if entries else now,
            "duration": (entries[-1]["timestamp"] - entries[0]["timestamp"]) if len(entries) > 1 else 0,
            "entry_count": len(entries),
            "first_x": first_x,
            "final_y": final_y,
            "root_xy": chain.get("root_xy"),
            "head_xy": chain.get("head_xy"),
            "all_verified": verification["valid"],
            "all_signatures_valid": True,
            "receipt_hash": receipt_hash,
            "agent_type": agent_type,
            "created_at": now,
        }

        self._receipts[receipt_id] = receipt
        return receipt

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        return self._receipts.get(receipt_id)

    def get_receipt_pdf_data(self, receipt_id: str) -> dict[str, Any] | None:
        receipt = self.get_receipt(receipt_id)
        if not receipt:
            return None
        return {
            "receipt": receipt,
            "format": "pdf",
            "generated_at": time.time(),
        }

    def get_receipt_badge(self, receipt_id: str) -> dict[str, Any] | None:
        receipt = self.get_receipt(receipt_id)
        if not receipt:
            return None
        verified = receipt.get("all_verified", False)
        return {
            "receipt_id": receipt_id,
            "verified": verified,
            "badge_url": f"https://api.pruv.dev/v1/receipts/{receipt_id}/badge",
            "svg": _generate_badge_svg(verified, receipt.get("entry_count", 0)),
        }


def _generate_badge_svg(verified: bool, entry_count: int) -> str:
    color = "#22c55e" if verified else "#ef4444"
    status = "verified" if verified else "unverified"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="20">'
        f'<rect width="80" height="20" fill="#555"/>'
        f'<rect x="80" width="80" height="20" fill="{color}"/>'
        f'<text x="40" y="14" fill="#fff" text-anchor="middle" '
        f'font-family="sans-serif" font-size="11">pruv</text>'
        f'<text x="120" y="14" fill="#fff" text-anchor="middle" '
        f'font-family="sans-serif" font-size="11">{status}</text>'
        f'</svg>'
    )


# Global instance
receipt_service = ReceiptService()
