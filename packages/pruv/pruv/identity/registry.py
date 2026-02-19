"""Identity storage backed by SQLite.

Stores agent identities and their XY chains.
The storage layer is an abstraction — SQLite is the default backend.
Replace this module to use any other persistent store.
"""

import json
import os
import sqlite3
from typing import Optional

from .chain import IdentityChain
from .models import AgentIdentity


class IdentityRegistry:
    """SQLite-backed storage for agent identities and their chains."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(".pruv", "identity.db")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS identities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    chain_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    chain_data TEXT NOT NULL
                )
                """
            )

    def save(self, identity: AgentIdentity, chain: IdentityChain) -> None:
        """Save or update an identity and its chain."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO identities
                (id, name, framework, owner, scope, purpose,
                 valid_from, valid_until, chain_id, created_at, status, chain_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identity.id,
                    identity.name,
                    identity.framework,
                    identity.owner,
                    json.dumps(identity.scope),
                    identity.purpose,
                    identity.valid_from,
                    identity.valid_until,
                    identity.chain_id,
                    identity.created_at,
                    identity.status,
                    json.dumps(chain.to_dict()),
                ),
            )

    def load(self, agent_id: str) -> Optional[tuple[AgentIdentity, IdentityChain]]:
        """Load an identity and its chain. Returns None if not found."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, name, framework, owner, scope, purpose, "
                "valid_from, valid_until, chain_id, created_at, status, chain_data "
                "FROM identities WHERE id = ?",
                (agent_id,),
            ).fetchone()
            if row is None:
                return None

            identity = AgentIdentity(
                id=row[0],
                name=row[1],
                framework=row[2],
                owner=row[3],
                scope=json.loads(row[4]),
                purpose=row[5],
                valid_from=row[6],
                valid_until=row[7],
                chain_id=row[8],
                created_at=row[9],
                status=row[10],
            )
            chain = IdentityChain.from_dict(json.loads(row[11]))
            return identity, chain

    def exists(self, agent_id: str) -> bool:
        """Check if an identity exists."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM identities WHERE id = ?", (agent_id,)
            ).fetchone()
            return row is not None

    def list_all(self) -> list[AgentIdentity]:
        """List all stored identities (without chain data)."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, name, framework, owner, scope, purpose, "
                "valid_from, valid_until, chain_id, created_at, status "
                "FROM identities ORDER BY created_at DESC"
            ).fetchall()
            return [
                AgentIdentity(
                    id=row[0],
                    name=row[1],
                    framework=row[2],
                    owner=row[3],
                    scope=json.loads(row[4]),
                    purpose=row[5],
                    valid_from=row[6],
                    valid_until=row[7],
                    chain_id=row[8],
                    created_at=row[9],
                    status=row[10],
                )
                for row in rows
            ]
