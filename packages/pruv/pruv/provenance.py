"""pruv.provenance — Origin and chain of custody for digital artifacts.

Every digital artifact has an origin and a modification history.
pruv.provenance captures the origin state, chains every modification,
and produces a receipt proving the complete lifecycle.

Usage:
    import pruv

    # Register an artifact's origin
    artifact = pruv.provenance.origin(
        content=document_bytes,
        name="contract-v1.pdf",
        creator="legal@acme.com",
        api_key="pv_live_xxx"
    )

    # Record modifications
    pruv.provenance.transition(
        artifact.id,
        content=updated_bytes,
        modifier="counsel@partner.com",
        reason="Added clause 4.2"
    )

    # Verify the complete history
    result = pruv.provenance.verify(artifact.id)
    # origin intact · 1 modification · chain verified

    # Export as receipt
    receipt = pruv.provenance.receipt(artifact.id)
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Optional, Union

from pruv.client import PruvClient


def _hash_content(content: Union[bytes, str]) -> str:
    """Hash artifact content. Accepts bytes or string."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


@dataclass
class Artifact:
    """A tracked digital artifact."""

    id: str  # pa_ + hash of origin content
    name: str  # human-readable name
    content_hash: str  # SHA-256 of original content
    content_type: str  # file type or mime type
    creator: str  # who created it
    chain_id: str  # underlying pruv chain
    created_at: float  # timestamp
    current_hash: str  # hash of most recent version
    transition_count: int = 0  # number of modifications

    @property
    def fingerprint(self) -> str:
        """Short identifier."""
        return self.id[:14]


@dataclass
class ProvenanceVerification:
    """Result of verifying an artifact's provenance."""

    valid: bool
    artifact_id: str
    name: str
    origin_intact: bool  # first entry matches original hash
    chain_intact: bool  # all links verified
    transition_count: int
    current_hash: str
    message: str


class Provenance:
    """pruv.provenance module.

    Usage:
        import pruv
        artifact = pruv.provenance.origin(content, name="doc.pdf", api_key="pv_live_xxx")
        pruv.provenance.transition(artifact.id, content=new_content, modifier="alice")
        result = pruv.provenance.verify(artifact.id)
        receipt = pruv.provenance.receipt(artifact.id)
    """

    def __init__(self, api_key: str, endpoint: str = "https://api.pruv.dev") -> None:
        self.client = PruvClient(api_key=api_key, endpoint=endpoint)
        self._artifacts: dict[str, Artifact] = {}

    def origin(
        self,
        content: Union[bytes, str],
        name: str,
        creator: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, Any]] = None,
    ) -> Artifact:
        """Register a new artifact's origin.

        Hashes the content and creates a chain with the origin entry.
        This is the genesis — the provable starting point. Every
        subsequent transition chains from here.

        Args:
            content: The artifact's content (bytes or string)
            name: Human-readable name
            creator: Who created this artifact
            content_type: MIME type or file extension
            metadata: Optional additional metadata

        Returns:
            Artifact with ID, content hash, and chain ID
        """
        content_hash = _hash_content(content)

        # Derive artifact ID: pa_ + hash of content
        artifact_id = "pa_" + content_hash[:40]

        # Create provenance chain
        chain = self.client.create_chain(
            name=f"provenance:{name}",
            metadata={
                "type": "provenance",
                "artifact_name": name,
                "content_type": content_type,
                "creator": creator,
                "origin_hash": content_hash,
                **(metadata or {}),
            },
        )

        # Origin entry — the genesis of this artifact
        origin_data = {
            "action": "provenance.origin",
            "artifact_id": artifact_id,
            "name": name,
            "content_hash": content_hash,
            "content_type": content_type,
            "creator": creator,
            "created_at": time.time(),
            "metadata": metadata or {},
        }

        self.client.add_entry(
            chain_id=chain["id"],
            data=origin_data,
        )

        artifact = Artifact(
            id=artifact_id,
            name=name,
            content_hash=content_hash,
            content_type=content_type,
            creator=creator,
            chain_id=chain["id"],
            created_at=time.time(),
            current_hash=content_hash,
        )

        self._artifacts[artifact_id] = artifact
        return artifact

    def transition(
        self,
        artifact_id: str,
        content: Union[bytes, str],
        modifier: str,
        reason: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Record a modification to the artifact.

        Hashes the new content and appends a transition entry.
        The entry's X state is the previous hash. The Y state
        is the new hash. The chain links them.

        Args:
            artifact_id: The pa_ ID of the artifact
            content: The new content after modification
            modifier: Who made the modification
            reason: Why it was modified
            metadata: Optional additional metadata

        Returns:
            Entry receipt from pruv API
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise KeyError(f"Artifact not found: {artifact_id}")

        new_hash = _hash_content(content)
        previous_hash = artifact.current_hash

        transition_data = {
            "action": "provenance.transition",
            "artifact_id": artifact_id,
            "previous_hash": previous_hash,
            "new_hash": new_hash,
            "modifier": modifier,
            "reason": reason,
            "ts": time.time(),
            "metadata": metadata or {},
        }

        receipt = self.client.add_entry(
            chain_id=artifact.chain_id,
            data=transition_data,
        )

        artifact.current_hash = new_hash
        artifact.transition_count += 1

        return receipt

    def verify(self, artifact_id: str) -> ProvenanceVerification:
        """Verify an artifact's complete provenance.

        Checks:
        - Chain integrity (hash linking)
        - Origin entry exists with valid content hash
        - All transitions chain correctly (previous_hash matches)
        - Current hash matches last transition
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise KeyError(f"Artifact not found: {artifact_id}")

        chain_result = self.client.verify_chain(artifact.chain_id)
        chain_data = self.client.get_chain(artifact.chain_id)
        entries = chain_data.get("entries", [])

        chain_intact = chain_result.get("valid", False)

        # Check origin entry
        origin_intact = False
        if entries:
            origin_data = entries[0].get("data", {})
            origin_intact = origin_data.get("content_hash") == artifact.content_hash

        # Check transition chain
        transitions = entries[1:]  # skip origin
        transition_hashes_valid = True
        expected_hash = artifact.content_hash

        for t in transitions:
            t_data = t.get("data", {})
            if t_data.get("previous_hash") != expected_hash:
                transition_hashes_valid = False
                break
            expected_hash = t_data.get("new_hash", expected_hash)

        valid = chain_intact and origin_intact and transition_hashes_valid

        if valid:
            message = (
                f"✓ Provenance verified: {artifact.name} · "
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

        return ProvenanceVerification(
            valid=valid,
            artifact_id=artifact_id,
            name=artifact.name,
            origin_intact=origin_intact,
            chain_intact=chain_intact,
            transition_count=len(transitions),
            current_hash=artifact.current_hash,
            message=message,
        )

    def receipt(self, artifact_id: str) -> dict[str, Any]:
        """Generate a provenance receipt.

        Returns receipt data matching the universal pruv receipt schema.
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise KeyError(f"Artifact not found: {artifact_id}")

        verification = self.verify(artifact_id)
        chain_data = self.client.get_chain(artifact.chain_id)
        entries = chain_data.get("entries", [])

        # Build modification timeline
        modifications = []
        for entry in entries[1:]:
            e_data = entry.get("data", {})
            modifications.append(
                {
                    "modifier": e_data.get("modifier"),
                    "reason": e_data.get("reason"),
                    "previous_hash": e_data.get("previous_hash", "")[:12],
                    "new_hash": e_data.get("new_hash", "")[:12],
                    "timestamp": e_data.get("ts"),
                }
            )

        return {
            "pruv_version": "1.0",
            "type": "provenance",
            "chain_id": artifact.chain_id,
            "chain_intact": verification.chain_intact,
            "entries": len(entries),
            "verified": (
                f"{len(entries)}/{len(entries)}" if verification.valid else "failed"
            ),
            "timestamp": time.time(),
            "product_data": {
                "artifact_id": artifact_id,
                "name": artifact.name,
                "content_type": artifact.content_type,
                "creator": artifact.creator,
                "created_at": artifact.created_at,
                "origin_hash": artifact.content_hash,
                "current_hash": artifact.current_hash,
                "origin_intact": verification.origin_intact,
                "transition_count": verification.transition_count,
                "modifications": modifications,
            },
        }

    def history(self, artifact_id: str) -> list[dict[str, Any]]:
        """Get modification history for an artifact."""
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise KeyError(f"Artifact not found: {artifact_id}")

        chain_data = self.client.get_chain(artifact.chain_id)
        entries = chain_data.get("entries", [])
        return entries

    def lookup(self, artifact_id: str) -> Optional[Artifact]:
        """Look up a registered artifact."""
        return self._artifacts.get(artifact_id)
