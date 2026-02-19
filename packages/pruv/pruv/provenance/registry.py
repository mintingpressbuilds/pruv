"""Provenance storage backed by SQLite.

Stores artifacts and their XY chains.
The storage layer is an abstraction — SQLite is the default backend.
Replace this module to use any other persistent store.
"""

import json
import os
import sqlite3
from typing import Optional

from .chain import ProvenanceChain
from .models import Artifact


class ProvenanceRegistry:
    """SQLite-backed storage for artifacts and their chains."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(".pruv", "provenance.db")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    chain_id TEXT NOT NULL,
                    origin_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    current_state_hash TEXT NOT NULL,
                    chain_data TEXT NOT NULL
                )
                """
            )

    def save(self, artifact: Artifact, chain: ProvenanceChain) -> None:
        """Save or update an artifact and its chain."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifacts
                (id, name, classification, owner, chain_id,
                 origin_hash, created_at, current_state_hash, chain_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.id,
                    artifact.name,
                    artifact.classification,
                    artifact.owner,
                    artifact.chain_id,
                    artifact.origin_hash,
                    artifact.created_at,
                    artifact.current_state_hash,
                    json.dumps(chain.to_dict()),
                ),
            )

    def load(
        self, artifact_id: str
    ) -> Optional[tuple[Artifact, ProvenanceChain]]:
        """Load an artifact and its chain. Returns None if not found."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, name, classification, owner, chain_id, "
                "origin_hash, created_at, current_state_hash, chain_data "
                "FROM artifacts WHERE id = ?",
                (artifact_id,),
            ).fetchone()
            if row is None:
                return None

            artifact = Artifact(
                id=row[0],
                name=row[1],
                classification=row[2],
                owner=row[3],
                chain_id=row[4],
                origin_hash=row[5],
                created_at=row[6],
                current_state_hash=row[7],
            )
            chain = ProvenanceChain.from_dict(json.loads(row[8]))
            return artifact, chain

    def exists(self, artifact_id: str) -> bool:
        """Check if an artifact exists."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            return row is not None

    def list_all(self) -> list[Artifact]:
        """List all stored artifacts (without chain data)."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, name, classification, owner, chain_id, "
                "origin_hash, created_at, current_state_hash "
                "FROM artifacts ORDER BY created_at DESC"
            ).fetchall()
            return [
                Artifact(
                    id=row[0],
                    name=row[1],
                    classification=row[2],
                    owner=row[3],
                    chain_id=row[4],
                    origin_hash=row[5],
                    created_at=row[6],
                    current_state_hash=row[7],
                )
                for row in rows
            ]
