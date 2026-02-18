"""Receipt service — create, retrieve, and export receipts.

PostgreSQL-backed via SQLAlchemy.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from ..models.database import Base, Receipt, get_engine
from .chain_service import chain_service

logger = logging.getLogger("pruv.api.receipt_service")


def _receipt_to_dict(receipt: Receipt) -> dict[str, Any]:
    """Convert a Receipt ORM model to the dict format routes expect."""
    return {
        "id": receipt.id,
        "user_id": str(receipt.user_id) if receipt.user_id else None,
        "chain_id": receipt.chain_id,
        "task": receipt.task,
        "started": receipt.started,
        "completed": receipt.completed,
        "duration": receipt.duration,
        "entry_count": receipt.entry_count,
        "first_x": receipt.first_x,
        "final_y": receipt.final_y,
        "root_xy": receipt.root_xy,
        "head_xy": receipt.head_xy,
        "all_verified": receipt.all_verified if receipt.all_verified is not None else True,
        "all_signatures_valid": receipt.all_signatures_valid if receipt.all_signatures_valid is not None else True,
        "receipt_hash": receipt.receipt_hash,
        "agent_type": receipt.agent_type,
        "created_at": receipt.created_at.timestamp() if receipt.created_at else time.time(),
    }


class ReceiptService:
    """PostgreSQL-backed receipt service."""

    def __init__(self) -> None:
        self._session_factory: sessionmaker | None = None

    def init_db(self, database_url: str) -> None:
        """Initialize the database connection."""
        engine = get_engine(database_url)
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        logger.info("ReceiptService database initialized.")

    def _session(self) -> Session:
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return self._session_factory()

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

        receipt = Receipt(
            id=receipt_id,
            user_id=user_id,
            chain_id=chain_id,
            task=task,
            started=entries[0]["timestamp"] if entries else now,
            completed=entries[-1]["timestamp"] if entries else now,
            duration=(entries[-1]["timestamp"] - entries[0]["timestamp"]) if len(entries) > 1 else 0,
            entry_count=len(entries),
            first_x=first_x,
            final_y=final_y,
            root_xy=chain.get("root_xy"),
            head_xy=chain.get("head_xy"),
            all_verified=verification["valid"],
            all_signatures_valid=True,
            receipt_hash=receipt_hash,
            agent_type=agent_type,
            created_at=datetime.now(timezone.utc),
        )

        with self._session() as session:
            session.add(receipt)
            session.commit()
            session.refresh(receipt)
            return _receipt_to_dict(receipt)

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            receipt = session.query(Receipt).filter(Receipt.id == receipt_id).first()
            if not receipt:
                return None
            return _receipt_to_dict(receipt)

    def get_receipt_for_user(self, receipt_id: str, user_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            receipt = (
                session.query(Receipt)
                .filter(Receipt.id == receipt_id, Receipt.user_id == user_id)
                .first()
            )
            if not receipt:
                return None
            return _receipt_to_dict(receipt)

    def list_receipts(self, user_id: str) -> list[dict[str, Any]]:
        with self._session() as session:
            receipts = (
                session.query(Receipt)
                .filter(Receipt.user_id == user_id)
                .order_by(Receipt.created_at.desc())
                .all()
            )
            return [_receipt_to_dict(r) for r in receipts]

    def get_receipt_count(self, user_id: str) -> int:
        with self._session() as session:
            return session.query(Receipt).filter(Receipt.user_id == user_id).count()

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
