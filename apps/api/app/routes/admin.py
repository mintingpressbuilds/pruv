"""Admin routes for the pruv API.

Provides system status, monitoring, and administration endpoints.
These endpoints require admin-level API keys.
"""

from __future__ import annotations

import os
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import check_rate_limit, require_admin
from app.core.rate_limit import get_rate_limiter, PLAN_LIMITS, RateLimitResult
from app.middleware.logging import get_recent_logs, get_request_stats, get_slow_requests, get_error_requests

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
async def system_status(
    user: dict[str, Any] = Depends(require_admin),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Get overall system status."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "api_version": "2026-02-01",
        "environment": os.getenv("PRUV_ENV", "development"),
        "uptime_seconds": time.monotonic(),
        "features": {
            "chains": True,
            "checkpoints": True,
            "receipts": True,
            "webhooks": True,
            "signatures": True,
            "auto_redaction": True,
            "batch_append": True,
            "cloud_sync": True,
        },
        "limits": {
            "max_entries_per_chain": 100_000,
            "max_state_size_bytes": 1_048_576,
            "max_batch_size": 100,
            "max_chains_per_user_free": 10,
            "max_chains_per_user_pro": 100,
            "max_chains_per_user_team": 1_000,
        },
    }


@router.get("/metrics")
async def system_metrics(
    user: dict[str, Any] = Depends(require_admin),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Get system metrics and request statistics."""
    stats = get_request_stats()
    return {
        "requests": stats,
        "timestamp": time.time(),
    }


@router.get("/logs")
async def recent_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    type: str = Query(default="all", pattern=r"^(all|slow|errors)$"),
    user: dict[str, Any] = Depends(require_admin),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Get recent request logs."""

    if type == "slow":
        logs = get_slow_requests(limit=limit)
    elif type == "errors":
        logs = get_error_requests(limit=limit)
    else:
        logs = get_recent_logs(limit=limit)

    return {
        "logs": logs,
        "count": len(logs),
        "type": type,
    }


@router.get("/rate-limits")
async def rate_limit_info(
    user: dict[str, Any] = Depends(require_admin),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Get rate limit configuration."""
    return {
        "plans": {
            plan: {
                "requests_per_minute": limits["requests_per_minute"],
                "monthly_entries": limits["entries_per_month"],
            }
            for plan, limits in PLAN_LIMITS.items()
        },
    }


@router.get("/health/deep")
async def deep_health_check(
    user: dict[str, Any] = Depends(require_admin),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Perform a deep health check of all subsystems."""
    checks: dict[str, dict[str, Any]] = {}

    try:
        get_rate_limiter()
        checks["rate_limiter"] = {"status": "healthy", "type": "in_memory"}
    except Exception:
        checks["rate_limiter"] = {"status": "unhealthy"}

    try:
        test_path = "/tmp/pruv_health_check"
        with open(test_path, "w") as f:
            f.write("ok")
        with open(test_path, "r") as f:
            content = f.read()
        os.remove(test_path)
        checks["disk"] = {
            "status": "healthy" if content == "ok" else "unhealthy",
        }
    except Exception:
        checks["disk"] = {"status": "unhealthy"}

    try:
        import hashlib
        hashlib.sha256(b"pruv_health_check").hexdigest()
        checks["crypto"] = {"status": "healthy", "sha256": "available"}
    except Exception:
        checks["crypto"] = {"status": "unhealthy"}

    all_healthy = all(c["status"] == "healthy" for c in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": time.time(),
    }


@router.post("/cache/clear")
async def clear_cache(
    user: dict[str, Any] = Depends(require_admin),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Clear all caches."""
    rate_limiter = get_rate_limiter()
    rate_limiter.clear()

    return {
        "cleared": True,
        "caches": ["rate_limiter"],
        "timestamp": time.time(),
    }
