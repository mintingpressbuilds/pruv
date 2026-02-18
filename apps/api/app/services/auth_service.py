"""Authentication service — PostgreSQL-backed user management and API keys."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from ..core.security import generate_api_key, hash_api_key
from ..models.database import ApiKey, Base, User, get_engine

logger = logging.getLogger("pruv.api.auth")


class AuthService:
    """PostgreSQL-backed auth service for user and API key management."""

    def __init__(self) -> None:
        self._session_factory: sessionmaker | None = None

    def init_db(self, database_url: str) -> None:
        """Initialize the database connection."""
        engine = get_engine(database_url)
        Base.metadata.create_all(bind=engine)
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        logger.info("AuthService database initialized.")

    def _session(self) -> Session:
        if not self._session_factory:
            # Auto-initialize with SQLite for development/testing
            self.init_db("sqlite:///pruv_dev.db")
        return self._session_factory()

    # ──── Users ────

    def create_user(
        self,
        email: str,
        name: str | None = None,
        plan: str = "free",
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new user in the database."""
        user_id = user_id or uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)

        with self._session() as session:
            user = User(
                id=user_id,
                email=email,
                name=name or email.split("@")[0],
                plan=plan,
                entries_this_month=0,
                created_at=now,
                updated_at=now,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return self._user_to_dict(user)

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            return self._user_to_dict(user)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._session() as session:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                return None
            return self._user_to_dict(user)

    def ensure_user(self, user_id: str) -> dict[str, Any]:
        """Get or create a user by ID. Used for auto-provisioning."""
        existing = self.get_user(user_id)
        if existing:
            return existing
        try:
            return self.create_user(
                email=f"{user_id}@pruv.dev",
                name=f"User {user_id[:8]}",
                user_id=user_id,
            )
        except Exception:
            # Handle race condition or duplicate email/id
            existing = self.get_user(user_id)
            if existing:
                return existing
            return self.create_user(
                email=f"{user_id}_{uuid.uuid4().hex[:6]}@pruv.dev",
                name=f"User {user_id[:8]}",
                user_id=user_id,
            )

    def update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        with self._session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            for key, value in updates.items():
                if key in ("email", "name", "plan", "avatar_url"):
                    setattr(user, key, value)
            user.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(user)
            return self._user_to_dict(user)

    # ──── OAuth ────

    def get_or_create_oauth_user(
        self,
        provider: str,
        provider_id: str,
        email: str,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> dict[str, Any]:
        """Get or create a user from OAuth login."""
        with self._session() as session:
            # Check for existing OAuth link
            if provider == "github":
                user = session.query(User).filter(User.github_id == provider_id).first()
            elif provider == "google":
                user = session.query(User).filter(User.google_id == provider_id).first()
            else:
                user = None

            if user:
                return self._user_to_dict(user)

            # Check existing email
            user = session.query(User).filter(User.email == email).first()
            if user:
                if provider == "github":
                    user.github_id = provider_id
                elif provider == "google":
                    user.google_id = provider_id
                if avatar_url:
                    user.avatar_url = avatar_url
                session.commit()
                session.refresh(user)
                return self._user_to_dict(user)

            # Create new user
            user_id = uuid.uuid4().hex[:12]
            now = datetime.now(timezone.utc)
            user = User(
                id=user_id,
                email=email,
                name=name or email.split("@")[0],
                plan="free",
                entries_this_month=0,
                created_at=now,
                updated_at=now,
            )
            if provider == "github":
                user.github_id = provider_id
            elif provider == "google":
                user.google_id = provider_id
            if avatar_url:
                user.avatar_url = avatar_url
            session.add(user)
            session.commit()
            session.refresh(user)
            return self._user_to_dict(user)

    # ──── API Keys ────

    def create_api_key(
        self,
        user_id: str,
        name: str = "Default",
        scopes: list[str] | None = None,
        prefix: str = "pv_live_",
    ) -> dict[str, Any] | None:
        """Create a new API key. Returns the full key (only shown once)."""
        # Ensure user exists in database
        user = self.get_user(user_id)
        if not user:
            # Auto-provision user if they don't exist yet
            user = self.ensure_user(user_id)

        key = generate_api_key(prefix)
        key_hash = hash_api_key(key)
        key_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        resolved_scopes = scopes or ["read", "write"]

        with self._session() as session:
            api_key = ApiKey(
                id=key_id,
                user_id=user["id"],
                name=name,
                key_hash=key_hash,
                key_prefix=key[:12] + "\u2026",
                scopes=resolved_scopes,
                created_at=now,
            )
            session.add(api_key)
            session.commit()

        return {
            "id": key_id,
            "user_id": user["id"],
            "name": name,
            "key": key,
            "key_hash": key_hash,
            "key_prefix": key[:12] + "\u2026",
            "scopes": resolved_scopes,
            "created_at": time.time(),
            "last_used_at": None,
        }

    def get_user_by_api_key(self, api_key: str) -> dict[str, Any] | None:
        """Look up a user by their API key (checks the database)."""
        key_hash = hash_api_key(api_key)

        with self._session() as session:
            api_key_row = session.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
            if not api_key_row:
                return None

            # Update last_used_at
            api_key_row.last_used_at = datetime.now(timezone.utc)
            session.commit()

            user = session.query(User).filter(User.id == api_key_row.user_id).first()
            if not user:
                return None

            return {
                "id": str(user.id),
                "type": "api_key",
                "key_hash": key_hash,
                "plan": user.plan or "free",
                "scopes": api_key_row.scopes or ["read", "write"],
                "email": user.email,
                "name": user.name,
            }

    def auto_provision_api_key(self, api_key: str) -> dict[str, Any]:
        """Auto-provision a user and API key for a key that doesn't exist yet.

        This maintains backward compatibility: any valid-format key works
        on first use by creating the user and key record in the database.
        """
        key_hash = hash_api_key(api_key)
        user_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)

        with self._session() as session:
            # Create user
            user = User(
                id=user_id,
                email=f"{user_id}@pruv.dev",
                name=f"API User {user_id[:8]}",
                plan="free",
                entries_this_month=0,
                created_at=now,
                updated_at=now,
            )
            session.add(user)

            # Create api key record
            prefix = api_key[:12] + "\u2026"
            api_key_row = ApiKey(
                id=uuid.uuid4().hex[:12],
                user_id=user_id,
                name="Auto-provisioned",
                key_hash=key_hash,
                key_prefix=prefix,
                scopes=["read", "write"],
                created_at=now,
            )
            session.add(api_key_row)
            session.commit()

        return {
            "id": user_id,
            "type": "api_key",
            "key_hash": key_hash,
            "plan": "free",
            "scopes": ["read", "write"],
        }

    def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List all API keys for a user (without the actual keys)."""
        with self._session() as session:
            keys = session.query(ApiKey).filter(ApiKey.user_id == user_id).all()
            return [
                {
                    "id": str(k.id),
                    "name": k.name,
                    "key_prefix": k.key_prefix,
                    "scopes": k.scopes or ["read", "write"],
                    "created_at": k.created_at.timestamp() if k.created_at else time.time(),
                    "last_used_at": k.last_used_at.timestamp() if k.last_used_at else None,
                }
                for k in keys
            ]

    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke an API key."""
        with self._session() as session:
            api_key = (
                session.query(ApiKey)
                .filter(ApiKey.id == key_id, ApiKey.user_id == user_id)
                .first()
            )
            if not api_key:
                return False
            session.delete(api_key)
            session.commit()
            return True

    # ──── Usage Tracking ────

    def increment_entry_count(self, user_id: str, count: int = 1) -> bool:
        """Increment the monthly entry count. Returns True if under limit."""
        with self._session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            plan = user.plan or "free"
            limits = {
                "free": 1000,
                "pro": 50000,
                "team": 500000,
                "enterprise": 999999999,
            }
            max_entries = limits.get(plan, 1000)
            current = user.entries_this_month or 0

            if current + count > max_entries:
                return False

            user.entries_this_month = current + count
            session.commit()
            return True

    def get_usage(self, user_id: str) -> dict[str, Any]:
        """Get usage info for a user."""
        with self._session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}

            plan = user.plan or "free"
            limits = {
                "free": 1000,
                "pro": 50000,
                "team": 500000,
                "enterprise": 999999999,
            }
            max_entries = limits.get(plan, 1000)
            current = user.entries_this_month or 0

            return {
                "plan": plan,
                "entries_used": current,
                "entries_limit": max_entries,
                "entries_remaining": max(0, max_entries - current),
                "usage_percent": round((current / max_entries) * 100, 1) if max_entries > 0 else 0,
            }

    # ──── Helpers ────

    @staticmethod
    def _user_to_dict(user: User) -> dict[str, Any]:
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "plan": user.plan or "free",
            "entries_this_month": user.entries_this_month or 0,
            "created_at": user.created_at.timestamp() if user.created_at else time.time(),
            "avatar_url": user.avatar_url,
        }


# Global instance
auth_service = AuthService()
