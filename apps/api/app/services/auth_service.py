"""Authentication service — user management, API keys, OAuth."""

from __future__ import annotations

import time
import uuid
from typing import Any

from ..core.security import generate_api_key, hash_api_key


class AuthService:
    """In-memory auth service for user and API key management."""

    def __init__(self) -> None:
        self._users: dict[str, dict[str, Any]] = {}
        self._api_keys: dict[str, dict[str, Any]] = {}  # key_hash -> key info
        self._oauth_map: dict[str, str] = {}  # provider:id -> user_id

    def create_user(
        self,
        email: str,
        name: str | None = None,
        plan: str = "free",
    ) -> dict[str, Any]:
        """Create a new user."""
        user_id = uuid.uuid4().hex[:12]
        user = {
            "id": user_id,
            "email": email,
            "name": name or email.split("@")[0],
            "plan": plan,
            "entries_this_month": 0,
            "created_at": time.time(),
        }
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        for user in self._users.values():
            if user["email"] == email:
                return user
        return None

    def update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        user = self._users.get(user_id)
        if not user:
            return None
        for key, value in updates.items():
            if key in ("email", "name", "plan", "avatar_url"):
                user[key] = value
        return user

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
        oauth_key = f"{provider}:{provider_id}"

        if oauth_key in self._oauth_map:
            user_id = self._oauth_map[oauth_key]
            user = self._users.get(user_id)
            if user:
                return user

        # Check existing email
        existing = self.get_user_by_email(email)
        if existing:
            self._oauth_map[oauth_key] = existing["id"]
            existing[f"{provider}_id"] = provider_id
            if avatar_url:
                existing["avatar_url"] = avatar_url
            return existing

        # Create new user
        user = self.create_user(email=email, name=name)
        user[f"{provider}_id"] = provider_id
        if avatar_url:
            user["avatar_url"] = avatar_url
        self._oauth_map[oauth_key] = user["id"]
        return user

    # ──── API Keys ────

    def create_api_key(
        self,
        user_id: str,
        name: str = "Default",
        scopes: list[str] | None = None,
        prefix: str = "pv_live_",
    ) -> dict[str, Any] | None:
        """Create a new API key. Returns the full key (only shown once)."""
        user = self.get_user(user_id)
        if not user:
            return None

        key = generate_api_key(prefix)
        key_hash = hash_api_key(key)

        key_info = {
            "id": uuid.uuid4().hex[:12],
            "user_id": user_id,
            "name": name,
            "key_hash": key_hash,
            "key_prefix": key[:12] + "…",
            "scopes": scopes or ["read", "write"],
            "created_at": time.time(),
            "last_used_at": None,
        }
        self._api_keys[key_hash] = key_info

        return {
            **key_info,
            "key": key,  # Full key — only returned at creation
        }

    def get_user_by_api_key(self, api_key: str) -> dict[str, Any] | None:
        """Look up a user by their API key."""
        key_hash = hash_api_key(api_key)
        key_info = self._api_keys.get(key_hash)
        if not key_info:
            return None
        key_info["last_used_at"] = time.time()
        return self.get_user(key_info["user_id"])

    def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List all API keys for a user (without the actual keys)."""
        return [
            {
                "id": info["id"],
                "name": info["name"],
                "key_prefix": info["key_prefix"],
                "scopes": info["scopes"],
                "created_at": info["created_at"],
                "last_used_at": info["last_used_at"],
            }
            for info in self._api_keys.values()
            if info["user_id"] == user_id
        ]

    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke an API key."""
        for key_hash, info in list(self._api_keys.items()):
            if info["id"] == key_id and info["user_id"] == user_id:
                del self._api_keys[key_hash]
                return True
        return False

    # ──── Usage Tracking ────

    def increment_entry_count(self, user_id: str, count: int = 1) -> bool:
        """Increment the monthly entry count. Returns True if under limit."""
        user = self.get_user(user_id)
        if not user:
            return False

        plan = user.get("plan", "free")
        limits = {
            "free": 1000,
            "pro": 50000,
            "team": 500000,
            "enterprise": float("inf"),
        }
        max_entries = limits.get(plan, 1000)
        current = user.get("entries_this_month", 0)

        if current + count > max_entries:
            return False

        user["entries_this_month"] = current + count
        return True

    def get_usage(self, user_id: str) -> dict[str, Any]:
        """Get usage info for a user."""
        user = self.get_user(user_id)
        if not user:
            return {"error": "User not found"}

        plan = user.get("plan", "free")
        limits = {
            "free": 1000,
            "pro": 50000,
            "team": 500000,
            "enterprise": 999999999,
        }
        max_entries = limits.get(plan, 1000)
        current = user.get("entries_this_month", 0)

        return {
            "plan": plan,
            "entries_used": current,
            "entries_limit": max_entries,
            "entries_remaining": max(0, max_entries - current),
            "usage_percent": round((current / max_entries) * 100, 1) if max_entries > 0 else 0,
        }


# Global instance
auth_service = AuthService()
