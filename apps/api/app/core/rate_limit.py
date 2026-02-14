"""Rate limiting via sliding window."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

PLAN_LIMITS = {
    "free": {"requests_per_minute": 60, "entries_per_month": 1000},
    "pro": {"requests_per_minute": 300, "entries_per_month": 50000},
    "team": {"requests_per_minute": 1000, "entries_per_month": 500000},
    "enterprise": {"requests_per_minute": 10000, "entries_per_month": float("inf")},
}


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: float

    def to_headers(self) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at)),
        }


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter.

    In production, this should be backed by Redis.
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, plan: str = "free") -> RateLimitResult:
        """Check if a request is allowed under the rate limit."""
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        max_requests = limits["requests_per_minute"]
        window = 60.0  # 1 minute

        now = time.time()
        window_start = now - window

        # Clean old entries
        self._windows[key] = [
            t for t in self._windows[key] if t > window_start
        ]

        current_count = len(self._windows[key])
        allowed = current_count < max_requests

        if allowed:
            self._windows[key].append(now)

        oldest = self._windows[key][0] if self._windows[key] else now
        reset_at = oldest + window

        return RateLimitResult(
            allowed=allowed,
            limit=int(max_requests),
            remaining=max(0, int(max_requests) - current_count - (1 if allowed else 0)),
            reset_at=reset_at,
        )

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        self._windows.pop(key, None)

    def clear(self) -> None:
        """Clear all rate limit windows."""
        self._windows.clear()


# Global instance
rate_limiter = SlidingWindowRateLimiter()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Get the global rate limiter instance."""
    return rate_limiter
