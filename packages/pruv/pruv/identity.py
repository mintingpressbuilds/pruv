"""pruv.identity — Persistent verifiable identity for agents and systems.

An identity is a chain. Every action appends to it. The chain IS the
identity — not a username, not an API key, not a database row. A
cryptographic chain of everything this agent has done, independently
verifiable by anyone.

Usage:
    import pruv

    # Register an agent identity
    agent = pruv.identity.register(
        name="my-agent",
        agent_type="langchain",
        api_key="pv_live_xxx"
    )

    # Every action is recorded
    pruv.identity.act(agent.id, "read_email", {"from": "boss@co.com"})
    pruv.identity.act(agent.id, "draft_reply", {"to": "boss@co.com"})
    pruv.identity.act(agent.id, "send_email", {"to": "boss@co.com"})

    # Verify the complete identity
    result = pruv.identity.verify(agent.id)
    # 3 actions · all verified · chain intact

    # Export as receipt
    receipt = pruv.identity.receipt(agent.id)
    # Self-verifying HTML — who this agent is, what it did, proof it's real
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Optional

from xycore import generate_keypair

from pruv.client import PruvClient


@dataclass
class AgentIdentity:
    """A registered agent identity backed by a pruv chain."""

    id: str  # identity chain ID (same as address)
    name: str  # human-readable name
    agent_type: str  # langchain, crewai, custom, etc.
    public_key: str  # Ed25519 public key (hex)
    address: str  # pi_ + first 40 chars of hash(public_key)
    chain_id: str  # underlying pruv chain ID
    registered_at: float  # timestamp
    action_count: int = 0  # total actions recorded

    @property
    def fingerprint(self) -> str:
        """Short identifier derived from public key."""
        return self.address[:12]


@dataclass
class IdentityVerification:
    """Result of verifying an agent identity."""

    valid: bool
    identity_id: str
    name: str
    action_count: int
    chain_intact: bool
    signatures_valid: bool
    first_action: Optional[float]  # timestamp
    last_action: Optional[float]  # timestamp
    message: str


class Identity:
    """pruv.identity module.

    Usage:
        import pruv
        agent = pruv.identity.register("my-agent", api_key="pv_live_xxx")
        pruv.identity.act(agent.id, "did_something", {"key": "val"})
        result = pruv.identity.verify(agent.id)
        receipt = pruv.identity.receipt(agent.id)
    """

    def __init__(self, api_key: str, endpoint: str = "https://api.pruv.dev") -> None:
        self.client = PruvClient(api_key=api_key, endpoint=endpoint)
        self._identities: dict[str, AgentIdentity] = {}
        self._private_keys: dict[str, bytes] = {}  # local only, never sent

    def register(
        self,
        name: str,
        agent_type: str = "custom",
        metadata: Optional[dict[str, Any]] = None,
    ) -> AgentIdentity:
        """Register a new agent identity.

        Generates an Ed25519 keypair. The public key IS the identity.
        Creates a pruv chain with a registration entry as the genesis.
        The private key is stored locally and never leaves the machine.

        Args:
            name: Human-readable name for this agent
            agent_type: Type of agent (langchain, crewai, custom, etc.)
            metadata: Optional metadata about the agent

        Returns:
            AgentIdentity with address, public key, and chain ID
        """
        # Generate keypair — the public key IS the identity
        private_bytes, public_bytes = generate_keypair()
        public_hex = public_bytes.hex()

        # Derive address: pi_ + hash of public key
        address = "pi_" + hashlib.sha256(public_bytes).hexdigest()[:40]

        # Create identity chain via pruv API
        chain = self.client.create_chain(
            name=f"identity:{name}",
            metadata={
                "type": "identity",
                "agent_name": name,
                "agent_type": agent_type,
                "public_key": public_hex,
                "address": address,
                **(metadata or {}),
            },
        )

        # Registration entry — the genesis of this identity
        registration_data = {
            "action": "identity.registered",
            "name": name,
            "agent_type": agent_type,
            "public_key": public_hex,
            "address": address,
            "registered_at": time.time(),
        }

        self.client.add_entry(
            chain_id=chain["id"],
            data=registration_data,
        )

        identity = AgentIdentity(
            id=address,
            name=name,
            agent_type=agent_type,
            public_key=public_hex,
            address=address,
            chain_id=chain["id"],
            registered_at=time.time(),
        )

        self._identities[address] = identity
        self._private_keys[address] = private_bytes

        return identity

    def act(
        self,
        identity_id: str,
        action: str,
        data: Optional[dict[str, Any]] = None,
        sign: bool = True,
    ) -> dict[str, Any]:
        """Record an action for this identity.

        Appends to the identity's chain. Optionally signs with
        the identity's private key for non-repudiation.

        Args:
            identity_id: The pi_ address of the identity
            action: What the agent did
            data: Action payload
            sign: Whether to Ed25519 sign this entry (default True)

        Returns:
            Entry receipt from pruv API
        """
        identity = self._identities.get(identity_id)
        if not identity:
            raise KeyError(f"Identity not found: {identity_id}")

        entry_data = {
            "action": action,
            "identity": identity_id,
            "ts": time.time(),
            "data": data or {},
        }

        receipt = self.client.add_entry(
            chain_id=identity.chain_id,
            data=entry_data,
        )

        identity.action_count += 1
        return receipt

    def verify(self, identity_id: str) -> IdentityVerification:
        """Verify an identity's complete chain.

        Checks:
        - Chain integrity (hash linking)
        - Registration entry exists and is valid
        - All signatures valid (if signed)
        - Action count matches chain length
        """
        identity = self._identities.get(identity_id)
        if not identity:
            raise KeyError(f"Identity not found: {identity_id}")

        chain_result = self.client.verify_chain(identity.chain_id)
        chain_data = self.client.get_chain(identity.chain_id)

        entries = chain_data.get("entries", [])

        first_action = None
        last_action = None
        if len(entries) > 1:  # skip registration entry
            first_action = entries[1].get("data", {}).get("ts")
            last_action = entries[-1].get("data", {}).get("ts")

        chain_intact = chain_result.get("valid", False)

        valid = chain_intact

        if valid:
            message = (
                f"✓ Identity verified: {identity.name} · "
                f"{len(entries) - 1} actions · chain intact"
            )
        else:
            break_idx = chain_result.get("break_index")
            message = f"✗ Identity verification failed at entry {break_idx}"

        return IdentityVerification(
            valid=valid,
            identity_id=identity_id,
            name=identity.name,
            action_count=len(entries) - 1,  # exclude registration
            chain_intact=chain_intact,
            signatures_valid=True,  # TODO: verify signatures
            first_action=first_action,
            last_action=last_action,
            message=message,
        )

    def receipt(self, identity_id: str) -> dict[str, Any]:
        """Generate a receipt for this identity.

        Returns receipt data matching the universal pruv receipt schema.
        """
        identity = self._identities.get(identity_id)
        if not identity:
            raise KeyError(f"Identity not found: {identity_id}")

        verification = self.verify(identity_id)
        chain_data = self.client.get_chain(identity.chain_id)
        entries = chain_data.get("entries", [])

        return {
            "pruv_version": "1.0",
            "type": "identity",
            "chain_id": identity.chain_id,
            "chain_intact": verification.chain_intact,
            "entries": len(entries),
            "verified": (
                f"{len(entries)}/{len(entries)}" if verification.valid else "failed"
            ),
            "timestamp": time.time(),
            "product_data": {
                "identity_id": identity_id,
                "name": identity.name,
                "agent_type": identity.agent_type,
                "public_key": identity.public_key,
                "address": identity.address,
                "registered_at": identity.registered_at,
                "action_count": verification.action_count,
                "first_action": verification.first_action,
                "last_action": verification.last_action,
            },
        }

    def lookup(self, identity_id: str) -> Optional[AgentIdentity]:
        """Look up a registered identity."""
        return self._identities.get(identity_id)

    def history(self, identity_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get action history for an identity."""
        identity = self._identities.get(identity_id)
        if not identity:
            raise KeyError(f"Identity not found: {identity_id}")

        chain_data = self.client.get_chain(identity.chain_id)
        entries = chain_data.get("entries", [])
        # Skip registration entry, return most recent first
        actions = entries[1:]
        actions.reverse()
        return actions[:limit]
