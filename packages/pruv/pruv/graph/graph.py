"""Graph — deterministic state representation of a project with diff support."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..scanner.scanner import ScanResult


@dataclass
class FileChange:
    """A single file change between two graphs."""

    path: str
    change_type: str  # added, removed, modified
    old_hash: str | None = None
    new_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"path": self.path, "change_type": self.change_type}
        if self.old_hash:
            d["old_hash"] = self.old_hash
        if self.new_hash:
            d["new_hash"] = self.new_hash
        return d


@dataclass
class GraphDiff:
    """Diff between two graphs."""

    added: list[FileChange] = field(default_factory=list)
    removed: list[FileChange] = field(default_factory=list)
    modified: list[FileChange] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified)

    @property
    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.modified:
            parts.append(f"~{len(self.modified)} modified")
        return ", ".join(parts) if parts else "no changes"

    def to_dict(self) -> dict[str, Any]:
        return {
            "added": [f.to_dict() for f in self.added],
            "removed": [f.to_dict() for f in self.removed],
            "modified": [f.to_dict() for f in self.modified],
            "total_changes": self.total_changes,
            "summary": self.summary,
        }


@dataclass
class Graph:
    """Deterministic state representation of a project.

    The hash is computed from file paths, sizes, and line counts,
    producing a deterministic fingerprint.
    """

    root: str = ""
    files: list[dict[str, Any]] = field(default_factory=list)
    imports: list[dict[str, Any]] = field(default_factory=list)
    env_vars: list[dict[str, Any]] = field(default_factory=list)
    frameworks: list[dict[str, Any]] = field(default_factory=list)
    services: list[dict[str, Any]] = field(default_factory=list)
    file_contents: dict[str, str] = field(default_factory=dict)

    @property
    def hash(self) -> str:
        """Compute a deterministic hash of this graph."""
        data = {
            "files": sorted(self.files, key=lambda f: f["path"]),
            "imports": sorted([i["module"] for i in self.imports]),
            "env_vars": sorted([e["name"] for e in self.env_vars]),
            "frameworks": sorted([f["name"] for f in self.frameworks]),
            "services": sorted([s["name"] for s in self.services]),
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "hash": self.hash,
            "files": self.files,
            "imports": self.imports,
            "env_vars": self.env_vars,
            "frameworks": self.frameworks,
            "services": self.services,
            "file_count": len(self.files),
            "total_lines": sum(f.get("lines", 0) for f in self.files),
        }

    def to_state_dict(self) -> dict[str, Any]:
        """Convert to a dict suitable for hashing as X or Y state."""
        return {
            "graph_hash": self.hash,
            "file_count": len(self.files),
            "files": sorted([f["path"] for f in self.files]),
            "frameworks": sorted([f["name"] for f in self.frameworks]),
            "services": sorted([s["name"] for s in self.services]),
        }

    def diff(self, other: "Graph") -> GraphDiff:
        """Compute the diff between this graph and another."""
        result = GraphDiff()

        self_files = {f["path"]: f for f in self.files}
        other_files = {f["path"]: f for f in other.files}

        for path, info in other_files.items():
            if path not in self_files:
                result.added.append(FileChange(
                    path=path, change_type="added", new_hash=str(info.get("size", "")),
                ))
            else:
                old_info = self_files[path]
                if old_info.get("size") != info.get("size") or old_info.get("lines") != info.get("lines"):
                    result.modified.append(FileChange(
                        path=path, change_type="modified",
                        old_hash=str(old_info.get("size", "")),
                        new_hash=str(info.get("size", "")),
                    ))

        for path in self_files:
            if path not in other_files:
                result.removed.append(FileChange(
                    path=path, change_type="removed",
                    old_hash=str(self_files[path].get("size", "")),
                ))

        return result

    @classmethod
    def from_scan_result(cls, scan_result: "ScanResult") -> "Graph":
        """Create a Graph from a ScanResult."""
        return cls(
            root=scan_result.root,
            files=[f.to_dict() for f in scan_result.files],
            imports=[i.to_dict() for i in scan_result.imports],
            env_vars=[e.to_dict() for e in scan_result.env_vars],
            frameworks=[f.to_dict() for f in scan_result.frameworks],
            services=[s.to_dict() for s in scan_result.services],
            file_contents=scan_result.file_contents,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Graph":
        return cls(
            root=data.get("root", ""),
            files=data.get("files", []),
            imports=data.get("imports", []),
            env_vars=data.get("env_vars", []),
            frameworks=data.get("frameworks", []),
            services=data.get("services", []),
        )
