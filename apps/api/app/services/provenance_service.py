"""Provenance service — business logic for artifact origin, transitions, and verification."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from ..models.database import ArtifactRecord, Base, get_engine
from .chain_service import chain_service

logger = logging.getLogger("pruv.api.provenance_service")


def _artifact_to_dict(record: ArtifactRecord) -> dict[str, Any]:
    """Convert an ArtifactRecord ORM model to the dict format routes expect."""
    return {
        "id": record.id,
        "name": record.name,
        "content_hash": record.content_hash,
        "content_type": record.content_type or "application/octet-stream",
        "creator": record.creator,
        "chain_id": record.chain_id,
        "created_at": record.created_at,
        "current_hash": record.current_hash,
        "transition_count": record.transition_count or 0,
        "last_modified_at": record.last_modified_at,
        "metadata": record.metadata_ or {},
    }


class ProvenanceService:
    """PostgreSQL-backed provenance service."""

    def __init__(self) -> None:
        self._session_factory: sessionmaker | None = None

    def init_db(self, database_url: str) -> None:
        """Initialize the database connection."""
        engine = get_engine(database_url)
        Base.metadata.create_all(bind=engine)
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        logger.info("ProvenanceService database initialized.")

    def _session(self) -> Session:
        if not self._session_factory:
            self.init_db("sqlite:///pruv_dev.db")
        return self._session_factory()

    def register_origin(
        self,
        user_id: str,
        content_hash: str,
        name: str,
        creator: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a new artifact's origin.

        Only the hash is stored — the actual content never leaves the owner.
        """
        # Derive artifact ID: pa_ + first 40 chars of content hash
        artifact_id = "pa_" + content_hash[:40]

        # Create the underlying chain
        chain = chain_service.create_chain(
            user_id=user_id,
            name=f"provenance:{name}",
            chain_type="custom",
            tags=["provenance", content_type],
        )

        # Append origin entry
        chain_service.append_entry(
            chain_id=chain["id"],
            user_id=user_id,
            operation="provenance.origin",
            y_state={
                "action": "provenance.origin",
                "artifact_id": artifact_id,
                "name": name,
                "content_hash": content_hash,
                "content_type": content_type,
                "creator": creator,
            },
        )

        # Store artifact record
        now = datetime.now(timezone.utc)
        record = ArtifactRecord(
            id=artifact_id,
            user_id=user_id,
            name=name,
            content_hash=content_hash,
            content_type=content_type,
            creator=creator,
            chain_id=chain["id"],
            created_at=now,
            current_hash=content_hash,
            transition_count=0,
            metadata_=metadata or {},
        )

        with self._session() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _artifact_to_dict(record)

    def get_artifact(
        self, artifact_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Get an artifact by its pa_ address."""
        with self._session() as session:
            record = (
                session.query(ArtifactRecord)
                .filter(ArtifactRecord.id == artifact_id)
                .first()
            )
            if not record:
                return None
            if user_id and str(record.user_id) != user_id:
                return None
            return _artifact_to_dict(record)

    def list_artifacts(self, user_id: str) -> list[dict[str, Any]]:
        """List all artifacts for a user."""
        with self._session() as session:
            records = (
                session.query(ArtifactRecord)
                .filter(ArtifactRecord.user_id == user_id)
                .order_by(ArtifactRecord.created_at.desc())
                .all()
            )
            return [_artifact_to_dict(r) for r in records]

    def transition(
        self,
        artifact_id: str,
        user_id: str,
        new_hash: str,
        modifier: str,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Record a modification to an artifact."""
        with self._session() as session:
            record = (
                session.query(ArtifactRecord)
                .filter(ArtifactRecord.id == artifact_id)
                .first()
            )
            if not record:
                return None
            if str(record.user_id) != user_id:
                return None

            previous_hash = record.current_hash

            # Append transition entry to the artifact's chain
            entry = chain_service.append_entry(
                chain_id=record.chain_id,
                user_id=user_id,
                operation="provenance.transition",
                y_state={
                    "action": "provenance.transition",
                    "artifact_id": artifact_id,
                    "previous_hash": previous_hash,
                    "new_hash": new_hash,
                    "modifier": modifier,
                    "reason": reason,
                    "ts": time.time(),
                    "metadata": metadata or {},
                },
            )

            if not entry:
                return None

            # Update artifact stats
            record.current_hash = new_hash
            record.transition_count = (record.transition_count or 0) + 1
            record.last_modified_at = datetime.now(timezone.utc)
            session.commit()

            return entry

    def verify(self, artifact_id: str) -> dict[str, Any] | None:
        """Verify an artifact's provenance chain."""
        with self._session() as session:
            record = (
                session.query(ArtifactRecord)
                .filter(ArtifactRecord.id == artifact_id)
                .first()
            )
            if not record:
                return None

            chain_result = chain_service.verify_chain(record.chain_id)
            entries = chain_service.list_entries(
                record.chain_id, offset=0, limit=100000
            )

            chain_intact = chain_result.get("valid", False)

            # Check origin entry
            origin_intact = False
            if entries:
                origin_state = entries[0].get("y_state") or {}
                origin_intact = origin_state.get("content_hash") == record.content_hash

            # Check transition chain
            transitions = entries[1:]
            transition_hashes_valid = True
            expected_hash = record.content_hash

            for t in transitions:
                t_state = t.get("y_state") or {}
                if t_state.get("previous_hash") != expected_hash:
                    transition_hashes_valid = False
                    break
                expected_hash = t_state.get("new_hash", expected_hash)

            valid = chain_intact and origin_intact and transition_hashes_valid

            if valid:
                message = (
                    f"✓ Provenance verified: {record.name} · "
                    f"origin intact · {len(transitions)} modification(s) · "
                    f"chain verified"
                )
            else:
                parts = []
                if not chain_intact:
                    parts.append("chain broken")
                if not origin_intact:
                    parts.append("origin tampered")
                if not transition_hashes_valid:
                    parts.append("transition hash mismatch")
                message = f"✗ Provenance failed: {', '.join(parts)}"

            return {
                "valid": valid,
                "artifact_id": artifact_id,
                "name": record.name,
                "origin_intact": origin_intact,
                "chain_intact": chain_intact,
                "transition_count": len(transitions),
                "current_hash": record.current_hash,
                "message": message,
            }

    def get_history(
        self, artifact_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]] | None:
        """Get modification history for an artifact."""
        with self._session() as session:
            record = (
                session.query(ArtifactRecord)
                .filter(ArtifactRecord.id == artifact_id)
                .first()
            )
            if not record:
                return None

            entries = chain_service.list_entries(
                record.chain_id, offset=0, limit=100000
            )
            return entries[offset : offset + limit]


# Global instance
provenance_service = ProvenanceService()
