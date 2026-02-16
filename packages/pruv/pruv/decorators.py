"""Decorators for automatic action verification.

Usage:
    import pruv

    pruv.init("my-agent", api_key="pv_live_xxx")

    @pruv.verified
    def send_email(to, subject, body):
        smtp.send(to, subject, body)

    # Or with options:
    @pruv.verified(action_type="email.send", sensitive_keys=["body"])
    def send_email(to, subject, body):
        smtp.send(to, subject, body)
"""

from __future__ import annotations

import hashlib
import json
from functools import wraps
from typing import Any, Callable, TypeVar

from pruv.agent import Agent

F = TypeVar("F", bound=Callable[..., Any])

# Module-level default agent
_default_agent: Agent | None = None


def init(name: str, api_key: str, **kwargs: Any) -> Agent:
    """Initialize the default pruv agent.

    Returns the created Agent so callers can also hold a reference.
    """
    global _default_agent  # noqa: PLW0603
    _default_agent = Agent(name=name, api_key=api_key, **kwargs)
    return _default_agent


def verified(
    action_type: str | Callable[..., Any] | None = None,
    sensitive_keys: list[str] | None = None,
    agent: Agent | None = None,
) -> Any:
    """Decorator that records function calls as verified actions.

    Supports both bare ``@pruv.verified`` and parameterised
    ``@pruv.verified(action_type="x")`` forms.

    Before execution an ``<action>.start`` entry is appended.
    On success a ``<action>.complete`` entry with the result hash is
    appended.  On failure a ``<action>.error`` entry with the error
    details is appended and the exception is re-raised.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            target = agent or _default_agent
            if target is None:
                raise RuntimeError(
                    "No pruv agent initialized. Call pruv.init() first."
                )

            act = (
                action_type
                if isinstance(action_type, str)
                else f"{func.__module__}.{func.__name__}"
            )

            # Record intent before execution
            target.action(
                f"{act}.start",
                {
                    "function": func.__name__,
                    "args": _safe_serialize(args),
                    "kwargs": _safe_serialize(kwargs),
                    "status": "started",
                },
                sensitive_keys,
            )

            try:
                result = func(*args, **kwargs)

                target.action(
                    f"{act}.complete",
                    {
                        "function": func.__name__,
                        "status": "success",
                        "result_hash": _hash_result(result),
                    },
                    sensitive_keys,
                )
                return result

            except Exception as e:
                target.action(
                    f"{act}.error",
                    {
                        "function": func.__name__,
                        "status": "error",
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                raise

        return wrapper

    # Handle @pruv.verified without parentheses
    if callable(action_type):
        func = action_type
        action_type = None
        return decorator(func)

    return decorator


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _safe_serialize(obj: Any) -> Any:
    """Serialize args/kwargs safely, replacing non-serializable objects."""
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _hash_result(result: Any) -> str:
    """Hash the result for verification without storing raw content."""
    try:
        raw = json.dumps(result, sort_keys=True, default=str)
    except (TypeError, ValueError):
        raw = str(result)
    return hashlib.sha256(raw.encode()).hexdigest()
