"""Identity service — business logic for agent identity CRUD and verification."""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from ..models.database import Base, Chain, Entry, IdentityRecord, get_engine
from .chain_service import chain_service

logger = logging.getLogger("pruv.api.identity_service")


def _identity_to_dict(record: IdentityRecord) -> dict[str, Any]:
    """Convert an IdentityRecord ORM model to the dict format routes expect."""
    return {
        "id": record.id,
        "name": record.name,
        "agent_type": record.agent_type or "custom",
        "owner": record.owner or "",
        "scope": record.scope or [],
        "purpose": record.purpose or "",
        "valid_from": record.valid_from,
        "valid_until": record.valid_until,
        "public_key": record.public_key,
        "chain_id": record.chain_id,
        "registered_at": record.registered_at,
        "action_count": record.action_count or 0,
        "last_action_at": record.last_action_at,
        "metadata": record.metadata_ or {},
    }


class IdentityService:
    """PostgreSQL-backed identity service."""

    def __init__(self) -> None:
        self._session_factory: sessionmaker | None = None

    def init_db(self, database_url: str) -> None:
        """Initialize the database connection."""
        engine = get_engine(database_url)
        Base.metadata.create_all(bind=engine)
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        logger.info("IdentityService database initialized.")

    def _session(self) -> Session:
        if not self._session_factory:
            self.init_db("sqlite:///pruv_dev.db")
        return self._session_factory()

    def register(
        self,
        user_id: str,
        name: str,
        agent_type: str = "custom",
        owner: str = "",
        scope: list[str] | None = None,
        purpose: str = "",
        valid_from: str | None = None,
        valid_until: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a new agent identity.

        Creates a chain, generates a keypair, stores the identity record,
        and appends the registration entry.
        """
        # Generate Ed25519 keypair
        try:
            from xycore import generate_keypair
            private_bytes, public_bytes = generate_keypair()
            public_hex = public_bytes.hex()
        except Exception:
            # Fallback: use random bytes if crypto not available
            random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
            public_hex = random_bytes.hex()
            public_bytes = random_bytes

        # Derive address: pi_ + hash of public key
        if isinstance(public_bytes, str):
            public_bytes = bytes.fromhex(public_bytes)
        address = "pi_" + hashlib.sha256(public_bytes).hexdigest()[:40]

        # Create the underlying chain
        chain = chain_service.create_chain(
            user_id=user_id,
            name=f"identity:{name}",
            chain_type="custom",
            tags=["identity", agent_type],
        )

        # Append registration entry
        chain_service.append_entry(
            chain_id=chain["id"],
            user_id=user_id,
            operation="identity.registered",
            y_state={
                "action": "identity.registered",
                "name": name,
                "agent_type": agent_type,
                "owner": owner,
                "scope": scope or [],
                "purpose": purpose,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "public_key": public_hex,
                "address": address,
            },
        )

        # Store identity record
        now = datetime.now(timezone.utc)
        record = IdentityRecord(
            id=address,
            user_id=user_id,
            name=name,
            agent_type=agent_type,
            owner=owner,
            scope=scope or [],
            purpose=purpose,
            valid_from=valid_from,
            valid_until=valid_until,
            public_key=public_hex,
            chain_id=chain["id"],
            registered_at=now,
            action_count=0,
            metadata_=metadata or {},
        )

        with self._session() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            result = _identity_to_dict(record)

        return result

    def get_identity(
        self, identity_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Get an identity by its pi_ address."""
        with self._session() as session:
            record = (
                session.query(IdentityRecord)
                .filter(IdentityRecord.id == identity_id)
                .first()
            )
            if not record:
                return None
            if user_id and str(record.user_id) != user_id:
                return None
            return _identity_to_dict(record)

    def list_identities(self, user_id: str) -> list[dict[str, Any]]:
        """List all identities for a user."""
        with self._session() as session:
            records = (
                session.query(IdentityRecord)
                .filter(IdentityRecord.user_id == user_id)
                .order_by(IdentityRecord.registered_at.desc())
                .all()
            )
            return [_identity_to_dict(r) for r in records]

    def act(
        self,
        identity_id: str,
        user_id: str,
        action: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Record an action for an identity."""
        with self._session() as session:
            record = (
                session.query(IdentityRecord)
                .filter(IdentityRecord.id == identity_id)
                .first()
            )
            if not record:
                return None
            if str(record.user_id) != user_id:
                return None

            # Append entry to the identity's chain
            entry = chain_service.append_entry(
                chain_id=record.chain_id,
                user_id=user_id,
                operation=action,
                y_state={
                    "action": action,
                    "identity": identity_id,
                    "ts": time.time(),
                    "data": data or {},
                },
            )

            if not entry:
                return None

            # Update identity stats
            record.action_count = (record.action_count or 0) + 1
            record.last_action_at = datetime.now(timezone.utc)
            session.commit()

            return entry

    def verify(self, identity_id: str) -> dict[str, Any] | None:
        """Verify an identity's chain."""
        with self._session() as session:
            record = (
                session.query(IdentityRecord)
                .filter(IdentityRecord.id == identity_id)
                .first()
            )
            if not record:
                return None

            chain_result = chain_service.verify_chain(record.chain_id)
            entries = chain_service.list_entries(record.chain_id, offset=0, limit=100000)

            chain_intact = chain_result.get("valid", False)
            action_count = max(len(entries) - 1, 0)  # exclude registration entry

            if chain_intact:
                message = (
                    f"✓ Identity verified: {record.name} · "
                    f"{action_count} actions · chain intact"
                )
            else:
                break_idx = chain_result.get("break_index")
                message = f"✗ Identity verification failed at entry {break_idx}"

            return {
                "valid": chain_intact,
                "identity_id": identity_id,
                "name": record.name,
                "action_count": action_count,
                "chain_intact": chain_intact,
                "message": message,
            }

    def get_history(
        self, identity_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]] | None:
        """Get action history for an identity."""
        with self._session() as session:
            record = (
                session.query(IdentityRecord)
                .filter(IdentityRecord.id == identity_id)
                .first()
            )
            if not record:
                return None

            entries = chain_service.list_entries(
                record.chain_id, offset=0, limit=100000
            )
            # Skip registration entry, reverse for most recent first
            actions = entries[1:]
            actions.reverse()
            # Apply pagination
            return actions[offset : offset + limit]


# Global instance
identity_service = IdentityService()
