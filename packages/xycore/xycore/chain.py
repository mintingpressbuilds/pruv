"""XYChain — an ordered sequence of XYEntries with verification."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .crypto import hash_state, verify_chain, verify_entry
from .entry import XYEntry
from .redact import redact_state
from .signature import sign_entry as _sign_entry, verify_signature

GENESIS = "GENESIS"


@dataclass
class XYChain:
    """An ordered chain of XY entries.

    The fundamental rule: Entry[N].x == Entry[N-1].y.
    First entry's x is ``GENESIS``.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "default"
    entries: list[XYEntry] = field(default_factory=list)

    # Configuration
    auto_redact: bool = True
    auto_checkpoint: bool = False
    checkpoint_interval: int = 20

    # Internal checkpoint callback (set by CheckpointManager)
    _checkpoint_callback: Any = field(default=None, repr=False)

    @property
    def length(self) -> int:
        """Number of entries in the chain."""
        return len(self.entries)

    @property
    def head(self) -> str:
        """Current Y value (the head of the chain)."""
        if not self.entries:
            return GENESIS
        return self.entries[-1].y

    @property
    def root(self) -> str | None:
        """The XY proof hash of the first entry."""
        if not self.entries:
            return None
        return self.entries[0].xy

    def append(
        self,
        operation: str,
        x_state: dict | None = None,
        y_state: dict | None = None,
        status: str = "success",
        metadata: dict | None = None,
        timestamp: float | None = None,
        private_key: bytes | None = None,
        signer_id: str | None = None,
    ) -> XYEntry:
        """Append a new entry to the chain.

        Automatically computes X from the previous Y (or GENESIS),
        hashes states, computes XY proof, and optionally signs.
        """
        # Auto-redact secrets
        if self.auto_redact:
            if x_state is not None:
                x_state = redact_state(x_state)
            if y_state is not None:
                y_state = redact_state(y_state)

        # Compute hashes
        x = self.head if self.entries else GENESIS
        if self.entries:
            x = self.entries[-1].y
        else:
            x = GENESIS

        x_hash = x
        y_hash = hash_state(y_state) if y_state is not None else hash_state({})

        ts = timestamp if timestamp is not None else time.time()
        index = len(self.entries)

        entry = XYEntry.create(
            index=index,
            operation=operation,
            x=x_hash,
            y=y_hash,
            x_state=x_state,
            y_state=y_state,
            status=status,
            metadata=metadata,
            timestamp=ts,
        )

        # Sign if key provided
        if private_key is not None:
            _sign_entry(entry, private_key, signer_id)

        self.entries.append(entry)

        # Auto-checkpoint
        if (
            self.auto_checkpoint
            and self._checkpoint_callback is not None
            and self.length % self.checkpoint_interval == 0
        ):
            self._checkpoint_callback(f"auto-checkpoint-{self.length}")

        return entry

    def verify(self) -> tuple[bool, int | None]:
        """Verify the entire chain. Returns (valid, break_index)."""
        return verify_chain(self.entries)

    def verify_signatures(self) -> tuple[bool, int | None]:
        """Verify all signatures in the chain.

        Returns (valid, first_invalid_index). Unsigned entries are skipped.
        """
        for i, entry in enumerate(self.entries):
            if entry.signature is not None:
                if not verify_signature(entry):
                    return False, i
        return True, None

    def get_entry(self, index: int) -> XYEntry | None:
        """Get an entry by index."""
        if 0 <= index < len(self.entries):
            return self.entries[index]
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize chain to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "entries": [e.to_dict() for e in self.entries],
            "auto_redact": self.auto_redact,
            "auto_checkpoint": self.auto_checkpoint,
            "checkpoint_interval": self.checkpoint_interval,
            "length": self.length,
            "head": self.head,
            "root": self.root,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "XYChain":
        """Deserialize chain from a dictionary."""
        chain = cls(
            id=data["id"],
            name=data["name"],
            auto_redact=data.get("auto_redact", True),
            auto_checkpoint=data.get("auto_checkpoint", False),
            checkpoint_interval=data.get("checkpoint_interval", 20),
        )
        chain.entries = [XYEntry.from_dict(e) for e in data.get("entries", [])]
        return chain

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: int) -> XYEntry:
        return self.entries[index]

    def __iter__(self):
        return iter(self.entries)
