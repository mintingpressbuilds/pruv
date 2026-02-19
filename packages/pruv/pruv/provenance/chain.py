"""ProvenanceChain — core XY chain wrapper for provenance operations.

Wraps xycore's XYChain to provide provenance-specific semantics.
All cryptography is handled by xycore. This module handles meaning.
"""

from xycore import XYChain


class ProvenanceChain:
    """A chain that represents an artifact's origin and modification history."""

    def __init__(self, chain: XYChain = None, name: str = "provenance"):
        self.chain = chain or XYChain(name=name)

    def origin(self, origin_data: dict) -> None:
        """Append origin entry as the first entry in the chain.

        X state: None — artifact did not exist.
        Y state: artifact origin data with content hash.
        """
        self.chain.append(
            operation="origin",
            x_state=None,
            y_state=origin_data,
        )

    def record_transition(self, x_state: dict, y_state: dict) -> int:
        """Append a transition entry to the chain.

        Returns the entry index.
        """
        entry = self.chain.append(
            operation="transition",
            x_state=x_state,
            y_state=y_state,
        )
        return entry.index

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
    def from_dict(cls, data: dict) -> "ProvenanceChain":
        chain = XYChain.from_dict(data)
        return cls(chain=chain)
