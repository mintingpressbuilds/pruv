"""IdentityChain — core XY chain wrapper for identity operations.

Wraps xycore's XYChain to provide identity-specific semantics.
All cryptography is handled by xycore. This module handles meaning.
"""

from xycore import XYChain


class IdentityChain:
    """A chain that represents an agent's identity and action history."""

    def __init__(self, chain: XYChain = None, name: str = "identity"):
        self.chain = chain or XYChain(name=name)

    def register(self, identity_data: dict) -> None:
        """Append registration entry as the first entry in the chain.

        X state: None — agent did not exist.
        Y state: full declared identity.
        """
        self.chain.append(
            operation="register",
            x_state=None,
            y_state=identity_data,
        )

    def record_action(self, x_state: dict, y_state: dict) -> int:
        """Append an action entry to the chain.

        Returns the entry index.
        """
        entry = self.chain.append(
            operation="act",
            x_state=x_state,
            y_state=y_state,
        )
        return entry.index

    def revoke(self, x_state: dict, y_state: dict) -> None:
        """Append a revocation entry to the chain."""
        self.chain.append(
            operation="revoke",
            x_state=x_state,
            y_state=y_state,
        )

    def verify(self) -> tuple[bool, int | None]:
        """Verify chain integrity. Returns (valid, break_index_or_None)."""
        return self.chain.verify()

    @property
    def entries(self):
        return self.chain.entries

    @property
    def head(self) -> str:
        """Current Y value — most recent state hash."""
        return self.chain.head

    @property
    def length(self) -> int:
        return self.chain.length

    def to_dict(self) -> dict:
        return self.chain.to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> "IdentityChain":
        chain = XYChain.from_dict(data)
        return cls(chain=chain)
