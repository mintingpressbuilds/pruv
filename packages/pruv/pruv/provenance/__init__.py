"""pruv.provenance — origin and chain of custody for digital artifacts.

Every transition requires an agent_id referencing a pruv.identity chain.
Verification cross-checks agent identity chains automatically.

Public interface:
    pruv.provenance.origin(...)      -> Artifact
    pruv.provenance.transition(...)  -> Transition
    pruv.provenance.verify(...)      -> ProvenanceVerificationResult
    pruv.provenance.receipt(...)     -> dict
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Union

from .chain import ProvenanceChain
from .models import Artifact, ProvenanceVerificationResult, Transition
from .receipt import generate_receipt
from .registry import ProvenanceRegistry

__all__ = [
    "origin",
    "transition",
    "verify",
    "receipt",
    "configure",
    "Artifact",
    "Transition",
    "ProvenanceVerificationResult",
]

# ─── Module State ────────────────────────────────────────────────────────────

_registry: Optional[ProvenanceRegistry] = None


def _get_registry() -> ProvenanceRegistry:
    global _registry
    if _registry is None:
        _registry = ProvenanceRegistry()
    return _registry


def configure(db_path: str = None) -> None:
    """Configure the storage backend.

    Args:
        db_path: Path to the SQLite database file.
                 Defaults to .pruv/provenance.db
    """
    global _registry
    _registry = ProvenanceRegistry(db_path=db_path)


def _reset() -> None:
    """Reset module state. Used for testing."""
    global _registry
    _registry = None


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _hash_content(content: Union[bytes, str, dict]) -> str:
    """Hash artifact content. Accepts bytes, string, or dict."""
    if isinstance(content, dict):
        import json

        content = json.dumps(content, sort_keys=True, separators=(",", ":"))
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _verify_agent(agent_id: str) -> dict:
    """Cross-verify an agent's identity chain.

    Returns a dict with agent details and verification status.
    Imports pruv.identity at call time to avoid circular imports.
    """
    from pruv.identity import verify as identity_verify
    from pruv.identity import _get_registry as identity_get_registry

    registry = identity_get_registry()
    loaded = registry.load(agent_id)
    if loaded is None:
        return {
            "exists": False,
            "name": "unknown",
            "owner": "unknown",
            "intact": False,
            "active": False,
            "in_scope": False,
        }

    agent, _ = loaded

    try:
        result = identity_verify(agent_id)
        return {
            "exists": True,
            "name": agent.name,
            "owner": agent.owner,
            "intact": result.intact,
            "active": result.active,
            "in_scope": result.intact and result.active,
        }
    except Exception:
        return {
            "exists": True,
            "name": agent.name,
            "owner": agent.owner,
            "intact": False,
            "active": False,
            "in_scope": False,
        }


# ─── Public Interface ───────────────────────────────────────────────────────


def origin(
    content: Union[bytes, str, dict],
    name: str,
    classification: str,
    owner: str,
    metadata: dict = None,
) -> Artifact:
    """Establish the origin of a digital artifact.

    Creates a new XY chain with an origin entry.
    X state: None — artifact did not exist.
    Y state: content hash + artifact metadata.

    The origin hash is the ground truth. Every subsequent
    transition is measured against it.

    Args:
        content: The artifact content (bytes, string, or dict).
        name: Human-readable artifact name.
        classification: "document", "dataset", "code", "model",
                        "communication", or "custom".
        owner: Who owns this artifact.
        metadata: Optional additional context.

    Returns:
        The registered Artifact.
    """
    registry = _get_registry()

    artifact_id = str(uuid.uuid4())
    content_hash = _hash_content(content)
    now = datetime.now(timezone.utc).isoformat()

    chain = ProvenanceChain(name=f"provenance-{name}")

    y_state = {
        "artifact_id": artifact_id,
        "name": name,
        "classification": classification,
        "owner": owner,
        "content_hash": content_hash,
        "metadata": metadata or {},
        "event": "origin",
    }

    chain.origin(y_state)

    artifact = Artifact(
        id=artifact_id,
        name=name,
        classification=classification,
        owner=owner,
        chain_id=chain.chain.id,
        origin_hash=content_hash,
        created_at=now,
        current_state_hash=content_hash,
    )

    registry.save(artifact, chain)
    return artifact


def transition(
    artifact_id: str,
    updated_content: Union[bytes, str, dict],
    agent_id: str,
    reason: str,
    metadata: dict = None,
) -> Transition:
    """Record a transition in an artifact's provenance chain.

    Every transition requires an agent_id and a reason.
    The agent's identity chain is cross-verified to determine
    authorization status.

    Does NOT block unauthorized transitions — records them.
    Detection is pruv's responsibility.

    Args:
        artifact_id: The artifact's UUID.
        updated_content: The artifact content after modification.
        agent_id: The pruv.identity agent UUID — required.
        reason: Declared reason for this modification — required.
        metadata: Optional additional context.

    Returns:
        The recorded Transition.

    Raises:
        ValueError: If the artifact is not found.
    """
    registry = _get_registry()
    loaded = registry.load(artifact_id)
    if loaded is None:
        raise ValueError(f"Artifact {artifact_id} not found")

    artifact, chain = loaded

    # Cross-verify agent identity
    agent_info = _verify_agent(agent_id)

    new_content_hash = _hash_content(updated_content)
    now = datetime.now(timezone.utc).isoformat()

    x_state = {
        "artifact_id": artifact_id,
        "content_hash": artifact.current_state_hash,
        "transition_count": chain.length - 1,  # subtract origin
        "chain_hash": chain.head,
    }

    y_state = {
        "artifact_id": artifact_id,
        "content_hash": new_content_hash,
        "agent_id": agent_id,
        "agent_name": agent_info["name"],
        "agent_owner": agent_info["owner"],
        "agent_verified": agent_info["intact"],
        "agent_active": agent_info["active"],
        "agent_in_scope": agent_info["in_scope"],
        "reason": reason,
        "transition_count": chain.length,
        "metadata": metadata or {},
        "event": "transition",
        "timestamp": now,
    }

    entry_index = chain.record_transition(x_state, y_state)

    # Update artifact state
    artifact.current_state_hash = new_content_hash
    registry.save(artifact, chain)

    return Transition(
        artifact_id=artifact_id,
        agent_id=agent_id,
        agent_name=agent_info["name"],
        agent_owner=agent_info["owner"],
        agent_in_scope=agent_info["in_scope"],
        reason=reason,
        content_hash_before=artifact.current_state_hash
        if entry_index == 1
        else x_state["content_hash"],
        content_hash_after=new_content_hash,
        metadata=metadata or {},
        timestamp=now,
        entry_index=entry_index,
    )


def verify(artifact_id: str) -> ProvenanceVerificationResult:
    """Verify an entire provenance chain.

    Cross-verifies each referenced agent identity chain.
    If an agent's identity chain is broken, that transition
    is flagged as unauthorized.

    Args:
        artifact_id: The artifact's UUID.

    Returns:
        A ProvenanceVerificationResult with complete details.

    Raises:
        ValueError: If the artifact is not found.
    """
    registry = _get_registry()
    loaded = registry.load(artifact_id)
    if loaded is None:
        raise ValueError(f"Artifact {artifact_id} not found")

    artifact, chain = loaded

    # Check chain integrity via xycore
    intact, break_at = chain.verify()

    # Count verified entries
    if intact:
        verified_count = chain.length
    elif break_at is not None:
        verified_count = break_at
    else:
        verified_count = 0

    # Analyze entries for transitions and agent verification
    transitions = []
    unauthorized = []
    break_at_agent = None
    break_detail = None

    for entry in chain.entries:
        if entry.y_state and entry.y_state.get("event") == "transition":
            agent_id = entry.y_state.get("agent_id", "")

            # Re-verify the agent at query time
            agent_info = _verify_agent(agent_id)
            agent_authorized = agent_info["in_scope"]

            t = Transition(
                artifact_id=artifact_id,
                agent_id=agent_id,
                agent_name=agent_info["name"],
                agent_owner=agent_info["owner"],
                agent_in_scope=agent_authorized,
                reason=entry.y_state.get("reason", ""),
                content_hash_before=entry.x_state.get("content_hash", "")
                if entry.x_state
                else "",
                content_hash_after=entry.y_state.get("content_hash", ""),
                metadata=entry.y_state.get("metadata", {}),
                timestamp=entry.y_state.get("timestamp", ""),
                entry_index=entry.index,
            )
            transitions.append(t)

            if not agent_authorized:
                unauthorized.append(t)

    # Build break detail if chain is broken
    if not intact and break_at is not None:
        broken_entry = (
            chain.entries[break_at] if break_at < len(chain.entries) else None
        )
        prev_entry = (
            chain.entries[break_at - 1]
            if break_at > 0 and break_at <= len(chain.entries)
            else None
        )

        # Identify responsible agent at break point
        if broken_entry and broken_entry.y_state:
            break_at_agent = broken_entry.y_state.get("agent_name")

        break_detail = {
            "expected_x": prev_entry.y if prev_entry else "GENESIS",
            "found_x": broken_entry.x if broken_entry else "N/A",
            "entry_timestamp": (
                datetime.fromtimestamp(
                    broken_entry.timestamp, tz=timezone.utc
                ).isoformat()
                if broken_entry
                else None
            ),
        }

    return ProvenanceVerificationResult(
        intact=intact,
        entries=chain.length,
        verified_count=verified_count,
        transitions=transitions,
        break_at=break_at,
        break_at_agent=break_at_agent,
        break_detail=break_detail,
        unauthorized_transitions=unauthorized,
    )


def receipt(artifact_id: str) -> dict:
    """Generate a universal receipt for a provenance chain.

    Automatically pulls and verifies the identity chain for each
    agent that touched the artifact. Output is readable by a
    non-technical party.

    Args:
        artifact_id: The artifact's UUID.

    Returns:
        Universal receipt dict with product_data and human_readable fields.

    Raises:
        ValueError: If the artifact is not found.
    """
    registry = _get_registry()
    loaded = registry.load(artifact_id)
    if loaded is None:
        raise ValueError(f"Artifact {artifact_id} not found")

    artifact, chain = loaded
    result = verify(artifact_id)

    return generate_receipt(artifact, chain, result)
