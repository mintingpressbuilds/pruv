"""Hash functions and verification for the XY primitive."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entry import XYEntry


def hash_state(state: dict) -> str:
    """Hash any state dict to produce an X or Y value.

    Uses canonical JSON (sorted keys, compact separators) for determinism.
    """
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_xy(x: str, operation: str, y: str, timestamp: float) -> str:
    """Compute the XY proof hash from x, operation, y, and timestamp.

    Returns a string in the format ``xy_{sha256_hex}``.
    """
    data = f"{x}:{operation}:{y}:{timestamp}"
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    return f"xy_{digest}"


def verify_entry(entry: "XYEntry") -> bool:
    """Verify that a single entry's XY proof is correct."""
    expected = compute_xy(entry.x, entry.operation, entry.y, entry.timestamp)
    return entry.xy == expected


def verify_chain(entries: "list[XYEntry]") -> tuple[bool, int | None]:
    """Verify an entire chain of entries.

    Returns (True, None) if valid, or (False, break_index) if broken.
    """
    for i, entry in enumerate(entries):
        if not verify_entry(entry):
            return False, i
        if i == 0:
            if entry.x != "GENESIS":
                return False, i
        else:
            if entry.x != entries[i - 1].y:
                return False, i
    return True, None
