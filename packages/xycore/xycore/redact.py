"""Auto-redaction of secrets in state dictionaries."""

from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"

# Patterns that indicate secret values by key name
SECRET_KEY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"private[_-]?key", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"access[_-]?key", re.IGNORECASE),
    re.compile(r"connection[_-]?string", re.IGNORECASE),
    re.compile(r"database[_-]?url", re.IGNORECASE),
    re.compile(r"dsn", re.IGNORECASE),
]

# Patterns that match secret values directly
SECRET_VALUE_PATTERNS: list[re.Pattern[str]] = [
    # Stripe keys
    re.compile(r"sk_live_[a-zA-Z0-9]+"),
    re.compile(r"sk_test_[a-zA-Z0-9]+"),
    re.compile(r"pk_live_[a-zA-Z0-9]+"),
    re.compile(r"pk_test_[a-zA-Z0-9]+"),
    # pruv keys
    re.compile(r"pv_live_[a-zA-Z0-9_-]+"),
    re.compile(r"pv_test_[a-zA-Z0-9_-]+"),
    # GitHub tokens
    re.compile(r"ghp_[a-zA-Z0-9]+"),
    re.compile(r"gho_[a-zA-Z0-9]+"),
    re.compile(r"ghs_[a-zA-Z0-9]+"),
    re.compile(r"ghr_[a-zA-Z0-9]+"),
    # AWS keys
    re.compile(r"AKIA[A-Z0-9]{16}"),
    # Slack tokens
    re.compile(r"xoxb-[a-zA-Z0-9-]+"),
    re.compile(r"xoxp-[a-zA-Z0-9-]+"),
    re.compile(r"xoxs-[a-zA-Z0-9-]+"),
    # PEM private keys
    re.compile(r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----"),
    re.compile(r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+EC\s+PRIVATE\s+KEY-----"),
    # Database connection strings
    re.compile(r"(?:postgresql|postgres|mysql|mongodb(?:\+srv)?|redis)://\S+"),
    # Generic patterns
    re.compile(r"(?:password|secret|token|api_key)\s*=\s*\S+", re.IGNORECASE),
]


def _is_secret_key(key: str) -> bool:
    """Check if a dictionary key looks like it holds a secret."""
    return any(p.search(key) for p in SECRET_KEY_PATTERNS)


def _redact_value(value: str) -> str:
    """Redact known secret patterns from a string value."""
    result = value
    for pattern in SECRET_VALUE_PATTERNS:
        result = pattern.sub(REDACTED, result)
    return result


def redact_state(state: Any, _depth: int = 0) -> Any:
    """Recursively redact secrets from a state object.

    - Dict keys matching secret patterns get their values replaced.
    - String values matching known secret formats are redacted inline.
    - Recurses into nested dicts and lists.
    """
    if _depth > 50:
        return state

    if isinstance(state, dict):
        result = {}
        for k, v in state.items():
            if isinstance(k, str) and _is_secret_key(k):
                result[k] = REDACTED
            else:
                result[k] = redact_state(v, _depth + 1)
        return result

    if isinstance(state, list):
        return [redact_state(item, _depth + 1) for item in state]

    if isinstance(state, str):
        return _redact_value(state)

    return state
