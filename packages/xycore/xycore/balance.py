"""Balance proof — cryptographic proof of a balance state change.

A payment transforms balances. BalanceProof hashes both sides
and creates a cryptographic proof linking them.

    Before:  Alice=$1000, Bob=$500
    After:   Alice=$750,  Bob=$750

    X  = hash(before)
    Y  = hash(after)
    XY = hash(X + "transfer" + Y + timestamp)

The proof is verifiable by anyone with the before/after data.
The chain rule (Entry[N].x == Entry[N-1].y) ensures sequential integrity.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .crypto import compute_xy, hash_state


@dataclass
class BalanceProof:
    """Cryptographic proof of a balance state change.

    Usage::

        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )

        proof.x          # hash of balances before
        proof.y          # hash of balances after
        proof.xy         # cryptographic proof
        proof.valid      # True
        proof.before     # {"alice": 1000.0, "bob": 500.0}
        proof.after      # {"alice": 750.0, "bob": 750.0}
        proof.delta      # {"alice": -250.0, "bob": +250.0}
    """

    before: dict[str, float]
    after: dict[str, float]
    amount: float
    sender: str
    recipient: str
    timestamp: float = field(default_factory=time.time)
    memo: Optional[str] = None

    # Computed on init
    x: str = ""
    y: str = ""
    xy: str = ""

    def __post_init__(self) -> None:
        self.x = hash_state(self._normalize(self.before))
        self.y = hash_state(self._normalize(self.after))
        self.xy = compute_xy(self.x, "transfer", self.y, self.timestamp)

    @classmethod
    def transfer(
        cls,
        balances: dict[str, float],
        sender: str,
        recipient: str,
        amount: float,
        memo: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> BalanceProof:
        """Create a balance proof for a transfer.

        Args:
            balances: Current balances for all parties involved.
            sender: Key in balances dict for sender.
            recipient: Key in balances dict for recipient.
            amount: Amount to transfer.
            memo: Optional memo/reference.
            timestamp: Optional timestamp (defaults to now).

        Raises:
            ValueError: If sender has insufficient balance or amount is not positive.
            KeyError: If sender not in balances.
        """
        if sender not in balances:
            raise KeyError(f"Sender '{sender}' not found in balances")
        if recipient not in balances:
            balances = {**balances, recipient: 0.0}

        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")

        if balances[sender] < amount:
            raise ValueError(
                f"Insufficient balance: {sender} has {balances[sender]}, "
                f"needs {amount}"
            )

        before = {sender: balances[sender], recipient: balances[recipient]}
        after = {
            sender: round(balances[sender] - amount, 8),
            recipient: round(balances[recipient] + amount, 8),
        }

        ts = timestamp or time.time()

        return cls(
            before=before,
            after=after,
            amount=amount,
            sender=sender,
            recipient=recipient,
            timestamp=ts,
            memo=memo,
        )

    @property
    def valid(self) -> bool:
        """Verify the proof by recomputing hashes."""
        expected_x = hash_state(self._normalize(self.before))
        expected_y = hash_state(self._normalize(self.after))
        expected_xy = compute_xy(expected_x, "transfer", expected_y, self.timestamp)
        return (
            self.x == expected_x
            and self.y == expected_y
            and self.xy == expected_xy
        )

    @property
    def delta(self) -> dict[str, float]:
        """Balance changes for each party."""
        return {
            party: round(self.after.get(party, 0) - self.before.get(party, 0), 8)
            for party in set(list(self.before.keys()) + list(self.after.keys()))
        }

    @property
    def balanced(self) -> bool:
        """Check that total in equals total out (conservation of value)."""
        return round(sum(self.delta.values()), 8) == 0.0

    def to_dict(self) -> dict:
        """Serialize proof to a dictionary."""
        return {
            "before": self.before,
            "after": self.after,
            "amount": self.amount,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "memo": self.memo,
            "x": self.x,
            "y": self.y,
            "xy": self.xy,
            "valid": self.valid,
            "balanced": self.balanced,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BalanceProof:
        """Deserialize proof from a dictionary."""
        return cls(
            before=data["before"],
            after=data["after"],
            amount=data["amount"],
            sender=data["sender"],
            recipient=data["recipient"],
            timestamp=data["timestamp"],
            memo=data.get("memo"),
        )

    @staticmethod
    def _normalize(balances: dict) -> dict:
        """Normalize balance dict for deterministic hashing."""
        return {k: str(round(v, 8)) for k, v in sorted(balances.items())}

    @staticmethod
    def verify_proof(proof_dict: dict) -> bool:
        """Verify a balance proof from its dict representation.

        Recomputes all hashes and checks they match.
        Anyone with the proof data can verify it.
        """
        proof = BalanceProof.from_dict(proof_dict)
        return proof.valid and proof.balanced
