"""Chain service — business logic for chain CRUD, verification, and sharing.

PostgreSQL-backed via SQLAlchemy.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from xycore import XYEntry, hash_state, verify_chain
from xycore.redact import redact_state

from ..models.database import Base, Chain, Entry, get_engine

logger = logging.getLogger("pruv.api.chain_service")


def _ts_to_float(dt: datetime | None) -> float:
    """Convert a datetime to a Unix timestamp float."""
    if dt is None:
        return time.time()
    return dt.timestamp()


def _chain_to_dict(chain: Chain) -> dict[str, Any]:
    """Convert a Chain ORM model to the dict format routes expect."""
    return {
        "id": chain.id,
        "user_id": str(chain.user_id) if chain.user_id else None,
        "name": chain.name,
        "description": chain.description,
        "tags": chain.tags or [],
        "chain_type": chain.chain_type or "custom",
        "length": chain.length or 0,
        "root_xy": chain.root_xy,
        "head_xy": chain.head_xy,
        "head_y": chain.head_y or "GENESIS",
        "auto_redact": chain.auto_redact if chain.auto_redact is not None else True,
        "share_id": chain.share_id,
        "created_at": _ts_to_float(chain.created_at),
        "updated_at": _ts_to_float(chain.updated_at),
    }


def _entry_to_dict(entry: Entry) -> dict[str, Any]:
    """Convert an Entry ORM model to the dict format routes expect."""
    return {
        "id": str(entry.id),
        "chain_id": entry.chain_id,
        "index": entry.index,
        "timestamp": entry.timestamp,
        "operation": entry.operation,
        "x": entry.x,
        "y": entry.y,
        "xy": entry.xy,
        "x_state": entry.x_state,
        "y_state": entry.y_state,
        "status": entry.status or "success",
        "verified": entry.verified if entry.verified is not None else True,
        "metadata": entry.metadata_ or {},
        "signature": entry.signature,
        "signer_id": entry.signer_id,
        "public_key": entry.public_key,
    }


class ChainService:
    """PostgreSQL-backed chain service."""

    def __init__(self) -> None:
        self._session_factory: sessionmaker | None = None

    def init_db(self, database_url: str) -> None:
        """Initialize the database connection."""
        engine = get_engine(database_url)
        Base.metadata.create_all(bind=engine)
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        logger.info("ChainService database initialized.")

    def _session(self) -> Session:
        if not self._session_factory:
            raise RuntimeError(
                "Database not initialized. Call init_db() first."
            )
        return self._session_factory()

    def create_chain(
        self, user_id: str, name: str, description: str | None = None,
        tags: list[str] | None = None, auto_redact: bool = True,
        chain_type: str = "custom",
    ) -> dict[str, Any]:
        chain_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)

        chain = Chain(
            id=chain_id,
            user_id=user_id,
            name=name,
            description=description,
            tags=tags or [],
            chain_type=chain_type,
            length=0,
            root_xy=None,
            head_xy=None,
            head_y="GENESIS",
            auto_redact=auto_redact,
            share_id=None,
            created_at=now,
            updated_at=now,
        )

        with self._session() as session:
            session.add(chain)
            session.commit()
            session.refresh(chain)
            return _chain_to_dict(chain)

    def get_chain(self, chain_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        with self._session() as session:
            chain = session.query(Chain).filter(Chain.id == chain_id).first()
            if not chain:
                return None
            if user_id and str(chain.user_id) != user_id:
                return None
            return _chain_to_dict(chain)

    def list_chains(self, user_id: str) -> list[dict[str, Any]]:
        with self._session() as session:
            chains = (
                session.query(Chain)
                .filter(Chain.user_id == user_id)
                .order_by(Chain.updated_at.desc())
                .all()
            )
            return [_chain_to_dict(c) for c in chains]

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
        with self._session() as session:
            chain = session.query(Chain).filter(Chain.id == chain_id).first()
            if not chain or (user_id and str(chain.user_id) != user_id):
                return None

            index = chain.length or 0

            # Auto-redact
            if chain.auto_redact is not False:
                if x_state:
                    x_state = redact_state(x_state)
                if y_state:
                    y_state = redact_state(y_state)

            # Compute hashes
            x = chain.head_y or "GENESIS"
            if index == 0:
                x = "GENESIS"

            y = hash_state(y_state) if y_state else hash_state({})
            ts = time.time()

            from xycore.crypto import compute_xy
            xy = compute_xy(x, operation, y, ts)

            entry = Entry(
                id=uuid.uuid4().hex[:12],
                chain_id=chain_id,
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
                metadata_=metadata or {},
                signature=signature,
                signer_id=signer_id,
                public_key=public_key,
            )

            session.add(entry)

            # Update chain
            chain.length = index + 1
            chain.head_xy = xy
            chain.head_y = y
            if index == 0:
                chain.root_xy = xy
            chain.updated_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(entry)
            return _entry_to_dict(entry)

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
        with self._session() as session:
            chain = session.query(Chain).filter(Chain.id == chain_id).first()
            if not chain or (user_id and str(chain.user_id) != user_id):
                return None
            for key, value in updates.items():
                if key in ("name", "description", "tags", "auto_redact", "chain_type"):
                    setattr(chain, key, value)
            chain.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(chain)
            return _chain_to_dict(chain)

    def delete_chain(self, chain_id: str, user_id: str) -> bool:
        with self._session() as session:
            chain = session.query(Chain).filter(Chain.id == chain_id).first()
            if not chain or (user_id and str(chain.user_id) != user_id):
                return False
            # Delete entries first (cascade should handle but be explicit)
            session.query(Entry).filter(Entry.chain_id == chain_id).delete()
            session.delete(chain)
            session.commit()
            return True

    def get_entry_by_index(self, chain_id: str, index: int) -> dict[str, Any] | None:
        with self._session() as session:
            entry = (
                session.query(Entry)
                .filter(Entry.chain_id == chain_id, Entry.index == index)
                .first()
            )
            if not entry:
                return None
            return _entry_to_dict(entry)

    def undo_last_entry(self, chain_id: str, user_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            chain = session.query(Chain).filter(Chain.id == chain_id).first()
            if not chain or (user_id and str(chain.user_id) != user_id):
                return None

            last_entry = (
                session.query(Entry)
                .filter(Entry.chain_id == chain_id)
                .order_by(Entry.index.desc())
                .first()
            )
            if not last_entry:
                return None

            removed = _entry_to_dict(last_entry)
            session.delete(last_entry)

            chain.length = max((chain.length or 1) - 1, 0)
            if chain.length > 0:
                prev_entry = (
                    session.query(Entry)
                    .filter(Entry.chain_id == chain_id)
                    .order_by(Entry.index.desc())
                    .first()
                )
                if prev_entry:
                    chain.head_xy = prev_entry.xy
                    chain.head_y = prev_entry.y
            else:
                chain.head_xy = None
                chain.head_y = "GENESIS"
                chain.root_xy = None
            chain.updated_at = datetime.now(timezone.utc)

            session.commit()
            return removed

    def get_chain_count(self, user_id: str) -> int:
        with self._session() as session:
            return session.query(Chain).filter(Chain.user_id == user_id).count()

    def get_entry_count(self, user_id: str) -> int:
        with self._session() as session:
            from sqlalchemy import func
            result = (
                session.query(func.coalesce(func.sum(Chain.length), 0))
                .filter(Chain.user_id == user_id)
                .scalar()
            )
            return int(result)

    def list_entries(self, chain_id: str, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        with self._session() as session:
            entries = (
                session.query(Entry)
                .filter(Entry.chain_id == chain_id)
                .order_by(Entry.index)
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [_entry_to_dict(e) for e in entries]

    def verify_chain(self, chain_id: str) -> dict[str, Any]:
        entries_data = self.list_entries(chain_id, offset=0, limit=100000)
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
        """Verify all payment entries in a chain."""
        from xycore.balance import BalanceProof

        entries_data = self.list_entries(chain_id, offset=0, limit=100000)

        payment_count = 0
        verified_count = 0
        breaks: list[int] = []
        balances: dict[str, float] = {}
        total_volume = 0.0

        for i, entry in enumerate(entries_data):
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
        with self._session() as session:
            chain = session.query(Chain).filter(Chain.id == chain_id).first()
            if not chain or (user_id and str(chain.user_id) != user_id):
                return None
            if not chain.share_id:
                chain.share_id = uuid.uuid4().hex[:12]
                session.commit()
                session.refresh(chain)
            return {
                "chain_id": chain_id,
                "share_id": chain.share_id,
                "share_url": f"https://app.pruv.dev/shared/{chain.share_id}",
            }

    def get_shared_chain(self, share_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
        with self._session() as session:
            chain = session.query(Chain).filter(Chain.share_id == share_id).first()
            if not chain:
                return None
            chain_dict = _chain_to_dict(chain)
            entries = (
                session.query(Entry)
                .filter(Entry.chain_id == chain.id)
                .order_by(Entry.index)
                .all()
            )
            entries_list = [_entry_to_dict(e) for e in entries]
            return chain_dict, entries_list


# Global instance
chain_service = ChainService()
