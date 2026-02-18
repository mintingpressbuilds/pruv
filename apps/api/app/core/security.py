"""Authentication and security utilities."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from .config import settings

API_KEY_PREFIX_LIVE = "pv_live_"
API_KEY_PREFIX_TEST = "pv_test_"


def generate_api_key(prefix: str = API_KEY_PREFIX_LIVE) -> str:
    """Generate a new API key with the given prefix + 32 random hex chars."""
    random_part = secrets.token_hex(16)
    return f"{prefix}{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage using SHA-256."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key_format(api_key: str) -> bool:
    """Check that an API key has a valid prefix."""
    return api_key.startswith(API_KEY_PREFIX_LIVE) or api_key.startswith(API_KEY_PREFIX_TEST)


def create_jwt_token(user_id: str, scopes: list[str] | None = None) -> str:
    """Create a JWT-like HMAC-signed token for a user."""
    payload = {
        "sub": user_id,
        "scopes": scopes or ["read", "write"],
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.jwt_expiration_hours * 3600,
    }
    payload_bytes = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    )
    sig = hmac.new(
        settings.jwt_secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return f"{payload_bytes.decode()}.{sig}"


def decode_jwt_token(token: str) -> dict[str, Any] | None:
    """Decode and verify an HMAC-signed token."""
    try:
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(
            settings.jwt_secret.encode(), payload_b64.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def extract_bearer_token(authorization: str | None) -> str | None:
    """Extract token from 'Bearer <token>' header."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None
