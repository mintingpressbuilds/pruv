"""Local JSON storage for XY chains."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .chain import XYChain


class LocalStorage:
    """Persist XY chains to local JSON files."""

    def __init__(self, directory: str | Path = ".pruv") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _chain_path(self, chain_id: str) -> Path:
        """Get the file path for a chain."""
        return self.directory / f"{chain_id}.json"

    def save(self, chain: XYChain) -> Path:
        """Save a chain to disk. Returns the file path."""
        path = self._chain_path(chain.id)
        data = chain.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, chain_id: str) -> XYChain:
        """Load a chain from disk."""
        path = self._chain_path(chain_id)
        if not path.exists():
            raise FileNotFoundError(f"Chain not found: {chain_id}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return XYChain.from_dict(data)

    def list_chains(self) -> list[dict[str, Any]]:
        """List all stored chains with basic info."""
        chains = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chains.append({
                    "id": data["id"],
                    "name": data["name"],
                    "length": data.get("length", 0),
                    "path": str(path),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return chains

    def delete(self, chain_id: str) -> bool:
        """Delete a chain file. Returns True if deleted."""
        path = self._chain_path(chain_id)
        if path.exists():
            os.remove(path)
            return True
        return False

    def exists(self, chain_id: str) -> bool:
        """Check if a chain exists on disk."""
        return self._chain_path(chain_id).exists()
