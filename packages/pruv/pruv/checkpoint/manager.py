"""Checkpoint manager — create, restore, preview, and auto-checkpoint."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from xycore import XYChain

from ..graph import Graph, GraphDiff
from ..scanner import scan as scan_dir

# Try zstandard for compression
_HAS_ZSTD = False
try:
    import zstandard
    _HAS_ZSTD = True
except ImportError:
    pass


@dataclass
class Checkpoint:
    """A point-in-time snapshot of chain state and optionally project files."""

    id: str
    name: str
    chain_id: str
    entry_index: int
    created_at: float
    chain_snapshot: dict[str, Any]
    graph_snapshot: dict[str, Any] | None = None
    file_snapshots: dict[str, str] | None = None
    compressed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "chain_id": self.chain_id,
            "entry_index": self.entry_index,
            "created_at": self.created_at,
            "chain_snapshot": self.chain_snapshot,
            "graph_snapshot": self.graph_snapshot,
            "compressed": self.compressed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        return cls(
            id=data["id"],
            name=data["name"],
            chain_id=data["chain_id"],
            entry_index=data["entry_index"],
            created_at=data["created_at"],
            chain_snapshot=data["chain_snapshot"],
            graph_snapshot=data.get("graph_snapshot"),
            compressed=data.get("compressed", False),
        )


@dataclass
class RestorePreview:
    """Preview of what will change if a checkpoint is restored."""

    checkpoint_id: str
    checkpoint_name: str
    current_entry_index: int
    target_entry_index: int
    entries_to_rollback: int
    diff: GraphDiff | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_name": self.checkpoint_name,
            "current_entry_index": self.current_entry_index,
            "target_entry_index": self.target_entry_index,
            "entries_to_rollback": self.entries_to_rollback,
        }
        if self.diff:
            d["diff"] = self.diff.to_dict()
        return d


class CheckpointManager:
    """Manage checkpoints for an XY chain."""

    def __init__(
        self,
        chain: XYChain,
        project_dir: str | Path | None = None,
        storage_dir: str | Path = ".pruv/checkpoints",
        compress: bool = True,
    ) -> None:
        self.chain = chain
        self.project_dir = Path(project_dir) if project_dir else None
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.compress = compress and _HAS_ZSTD
        self.checkpoints: list[Checkpoint] = []

        # Register auto-checkpoint callback
        self.chain._checkpoint_callback = lambda name: self.create(name)

    def create(self, name: str, include_files: bool = False) -> Checkpoint:
        """Create a checkpoint at the current chain state."""
        # Snapshot chain
        chain_data = self.chain.to_dict()

        # Snapshot graph
        graph_data = None
        file_snapshots = None
        if self.project_dir and self.project_dir.exists():
            graph = scan_dir(str(self.project_dir), include_contents=include_files)
            graph_data = graph.to_dict()
            if include_files:
                file_snapshots = graph.file_contents

        checkpoint = Checkpoint(
            id=uuid.uuid4().hex[:12],
            name=name,
            chain_id=self.chain.id,
            entry_index=self.chain.length - 1 if self.chain.length > 0 else -1,
            created_at=time.time(),
            chain_snapshot=chain_data,
            graph_snapshot=graph_data,
            file_snapshots=file_snapshots,
            compressed=self.compress,
        )

        self.checkpoints.append(checkpoint)
        self._save_checkpoint(checkpoint)
        return checkpoint

    def preview_restore(self, checkpoint_id: str) -> RestorePreview:
        """Preview what will change if restoring to a checkpoint."""
        checkpoint = self._find_checkpoint(checkpoint_id)
        current_index = self.chain.length - 1 if self.chain.length > 0 else -1

        diff = None
        if self.project_dir and checkpoint.graph_snapshot:
            current_graph = scan_dir(str(self.project_dir))
            old_graph = Graph.from_dict(checkpoint.graph_snapshot)
            diff = old_graph.diff(current_graph)

        return RestorePreview(
            checkpoint_id=checkpoint.id,
            checkpoint_name=checkpoint.name,
            current_entry_index=current_index,
            target_entry_index=checkpoint.entry_index,
            entries_to_rollback=max(0, current_index - checkpoint.entry_index),
            diff=diff,
        )

    def restore(self, checkpoint_id: str) -> XYChain:
        """Restore chain to a checkpoint state."""
        checkpoint = self._find_checkpoint(checkpoint_id)
        restored = XYChain.from_dict(checkpoint.chain_snapshot)
        self.chain.entries = restored.entries
        return self.chain

    def quick_undo(self) -> XYChain | None:
        """Restore to the most recent checkpoint."""
        if not self.checkpoints:
            return None
        latest = self.checkpoints[-1]
        return self.restore(latest.id)

    def list_checkpoints(self) -> list[dict[str, Any]]:
        """List all checkpoints."""
        return [
            {
                "id": cp.id,
                "name": cp.name,
                "entry_index": cp.entry_index,
                "created_at": cp.created_at,
            }
            for cp in self.checkpoints
        ]

    def _find_checkpoint(self, checkpoint_id: str) -> Checkpoint:
        for cp in self.checkpoints:
            if cp.id == checkpoint_id:
                return cp
        raise ValueError(f"Checkpoint not found: {checkpoint_id}")

    def _save_checkpoint(self, checkpoint: Checkpoint) -> Path:
        """Save checkpoint to disk."""
        data = json.dumps(checkpoint.to_dict(), indent=2).encode("utf-8")
        path = self.storage_dir / f"{checkpoint.id}.json"

        if self.compress and _HAS_ZSTD:
            cctx = zstandard.ZstdCompressor(level=3)
            data = cctx.compress(data)
            path = self.storage_dir / f"{checkpoint.id}.json.zst"

        with open(path, "wb") as f:
            f.write(data)

        return path

    def _load_checkpoint(self, checkpoint_id: str) -> Checkpoint:
        """Load checkpoint from disk."""
        # Try compressed first
        zst_path = self.storage_dir / f"{checkpoint_id}.json.zst"
        json_path = self.storage_dir / f"{checkpoint_id}.json"

        if zst_path.exists() and _HAS_ZSTD:
            with open(zst_path, "rb") as f:
                dctx = zstandard.ZstdDecompressor()
                data = dctx.decompress(f.read())
        elif json_path.exists():
            with open(json_path, "rb") as f:
                data = f.read()
        else:
            raise FileNotFoundError(f"Checkpoint not found on disk: {checkpoint_id}")

        return Checkpoint.from_dict(json.loads(data))
