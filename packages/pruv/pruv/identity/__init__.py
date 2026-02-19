"""pruv.identity — persistent verifiable identity for AI agents.

Public interface:
    pruv.identity.register(...)  -> AgentIdentity
    pruv.identity.act(...)       -> IdentityAction
    pruv.identity.verify(...)    -> VerificationResult
    pruv.identity.receipt(...)   -> dict
    pruv.identity.revoke(...)    -> AgentIdentity
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from .chain import IdentityChain
from .models import AgentIdentity, IdentityAction, VerificationResult
from .receipt import generate_receipt
from .registry import IdentityRegistry
from .scope import check_scope

__all__ = [
    "register",
    "act",
    "verify",
    "receipt",
    "revoke",
    "configure",
    "AgentIdentity",
    "IdentityAction",
    "VerificationResult",
]

# ─── Module State ────────────────────────────────────────────────────────────

_registry: Optional[IdentityRegistry] = None


def _get_registry() -> IdentityRegistry:
    global _registry
    if _registry is None:
        _registry = IdentityRegistry()
    return _registry


def configure(db_path: str = None) -> None:
    """Configure the storage backend.

    Args:
        db_path: Path to the SQLite database file.
                 Defaults to .pruv/identity.db
    """
    global _registry
    _registry = IdentityRegistry(db_path=db_path)


def _reset() -> None:
    """Reset module state. Used for testing."""
    global _registry
    _registry = None


# ─── Date Helpers ────────────────────────────────────────────────────────────


def _parse_datetime(s: str) -> datetime:
    """Parse an ISO 8601 date or datetime string into a timezone-aware datetime."""
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ─── Public Interface ───────────────────────────────────────────────────────


def register(
    name: str,
    framework: str,
    owner: str,
    scope: list[str],
    purpose: str,
    valid_until: str,
    valid_from: str = None,
    metadata: dict = None,
) -> AgentIdentity:
    """Register a new agent identity.

    Creates a new XY chain with a registration entry.
    X state: None — agent did not exist.
    Y state: full declared identity.

    Args:
        name: Human-readable agent name.
        framework: Agent framework ("crewai", "langchain", "openai", "custom").
        owner: Organization or individual accountable for this agent.
        scope: List of permitted operations (e.g. ["file.read", "file.write"]).
        purpose: Declared reason this agent exists.
        valid_until: ISO 8601 expiration date.
        valid_from: ISO 8601 start date. Defaults to now.
        metadata: Optional additional context.

    Returns:
        The registered AgentIdentity.
    """
    registry = _get_registry()

    agent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    if valid_from is None:
        valid_from = now

    chain = IdentityChain(name=f"identity-{name}")

    y_state = {
        "name": name,
        "framework": framework,
        "owner": owner,
        "scope": scope,
        "purpose": purpose,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "event": "registration",
    }
    if metadata:
        y_state["metadata"] = metadata

    chain.register(y_state)

    identity = AgentIdentity(
        id=agent_id,
        name=name,
        framework=framework,
        owner=owner,
        scope=scope,
        purpose=purpose,
        valid_from=valid_from,
        valid_until=valid_until,
        chain_id=chain.chain.id,
        created_at=now,
        status="active",
    )

    registry.save(identity, chain)
    return identity


def act(
    agent_id: str,
    action: str,
    action_scope: str,
    metadata: dict = None,
) -> IdentityAction:
    """Record an action on an identity chain.

    Does NOT block out-of-scope actions — records them.
    The chain is the record. Blocking is the caller's responsibility.
    Detection is pruv's responsibility.

    Args:
        agent_id: The agent's UUID.
        action: Description of what the agent did.
        action_scope: Which declared scope item this action maps to.
        metadata: Optional additional context.

    Returns:
        The recorded IdentityAction.

    Raises:
        ValueError: If the agent is not found.
    """
    registry = _get_registry()
    loaded = registry.load(agent_id)
    if loaded is None:
        raise ValueError(f"Agent {agent_id} not found")

    agent, chain = loaded

    in_scope = check_scope(action_scope, agent.scope)
    now = datetime.now(timezone.utc).isoformat()

    x_state = {
        "agent_id": agent_id,
        "previous_action_count": chain.length - 1,
        "chain_hash": chain.head,
    }

    y_state = {
        "agent_id": agent_id,
        "action": action,
        "action_scope": action_scope,
        "in_scope": in_scope,
        "action_count": chain.length,
        "metadata": metadata or {},
        "event": "action",
        "timestamp": now,
    }

    entry_index = chain.record_action(x_state, y_state)

    registry.save(agent, chain)

    return IdentityAction(
        agent_id=agent_id,
        action=action,
        action_scope=action_scope,
        in_scope=in_scope,
        metadata=metadata or {},
        timestamp=now,
        entry_index=entry_index,
    )


def verify(agent_id: str) -> VerificationResult:
    """Verify an entire identity chain.

    Returns the full picture — not just True/False.
    Reports chain integrity, scope compliance, validity period,
    and exact location of any break.

    Args:
        agent_id: The agent's UUID.

    Returns:
        A VerificationResult with complete details.

    Raises:
        ValueError: If the agent is not found.
    """
    registry = _get_registry()
    loaded = registry.load(agent_id)
    if loaded is None:
        raise ValueError(f"Agent {agent_id} not found")

    agent, chain = loaded

    # Check chain integrity via xycore
    intact, break_at = chain.verify()

    # Check validity period
    now = datetime.now(timezone.utc)
    try:
        vf = _parse_datetime(agent.valid_from)
        vu = _parse_datetime(agent.valid_until)
        active = vf <= now <= vu and agent.status == "active"
    except (ValueError, TypeError):
        active = agent.status == "active"

    # Count verified entries
    if intact:
        verified_count = chain.length
    elif break_at is not None:
        verified_count = break_at
    else:
        verified_count = 0

    # Analyze entries for scope
    in_scope_count = 0
    out_of_scope = []

    for entry in chain.entries:
        if entry.y_state and entry.y_state.get("event") == "action":
            if entry.y_state.get("in_scope"):
                in_scope_count += 1
            else:
                out_of_scope.append(
                    IdentityAction(
                        agent_id=agent_id,
                        action=entry.y_state.get("action", ""),
                        action_scope=entry.y_state.get("action_scope", ""),
                        in_scope=False,
                        metadata=entry.y_state.get("metadata", {}),
                        timestamp=entry.y_state.get("timestamp", ""),
                        entry_index=entry.index,
                    )
                )

    # Build break detail if chain is broken
    break_detail = None
    if not intact and break_at is not None:
        broken_entry = (
            chain.entries[break_at] if break_at < len(chain.entries) else None
        )
        prev_entry = (
            chain.entries[break_at - 1]
            if break_at > 0 and break_at <= len(chain.entries)
            else None
        )
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

    return VerificationResult(
        intact=intact,
        entries=chain.length,
        verified_count=verified_count,
        in_scope_count=in_scope_count,
        out_of_scope_actions=out_of_scope,
        break_at=break_at,
        break_detail=break_detail,
        active=active,
    )


def receipt(agent_id: str) -> dict:
    """Generate a universal receipt for an identity chain.

    Output is readable by a non-technical party.
    Includes both JSON receipt and human_readable string.

    Args:
        agent_id: The agent's UUID.

    Returns:
        Universal receipt dict with product_data and human_readable fields.

    Raises:
        ValueError: If the agent is not found.
    """
    registry = _get_registry()
    loaded = registry.load(agent_id)
    if loaded is None:
        raise ValueError(f"Agent {agent_id} not found")

    agent, chain = loaded
    result = verify(agent_id)

    return generate_receipt(agent, chain, result)


def revoke(agent_id: str, reason: str) -> AgentIdentity:
    """Revoke an agent identity.

    Appends a revocation entry to the chain.
    The chain remains intact and verifiable.
    Revocation is part of the record, not deletion.

    Args:
        agent_id: The agent's UUID.
        reason: Why this identity is being revoked.

    Returns:
        The updated AgentIdentity with status "revoked".

    Raises:
        ValueError: If the agent is not found or already revoked.
    """
    registry = _get_registry()
    loaded = registry.load(agent_id)
    if loaded is None:
        raise ValueError(f"Agent {agent_id} not found")

    agent, chain = loaded

    if agent.status == "revoked":
        raise ValueError(f"Agent {agent_id} is already revoked")

    now = datetime.now(timezone.utc).isoformat()

    x_state = {
        "agent_id": agent_id,
        "status": agent.status,
        "chain_hash": chain.head,
    }

    y_state = {
        "agent_id": agent_id,
        "status": "revoked",
        "reason": reason,
        "revoked_at": now,
        "event": "revocation",
    }

    chain.revoke(x_state, y_state)

    agent.status = "revoked"
    registry.save(agent, chain)

    return agent
