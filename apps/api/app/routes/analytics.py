"""Analytics routes for the pruv API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import check_rate_limit, get_current_user
from app.core.rate_limit import RateLimitResult
from app.services.analytics_service import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/usage")
async def get_usage_summary(
    days: int = Query(default=30, ge=1, le=365),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict:
    """Get usage summary for the current user."""
    service = get_analytics_service()
    return service.get_usage_summary(user["id"], days)


@router.get("/daily")
async def get_daily_usage(
    days: int = Query(default=30, ge=1, le=365),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> list[dict]:
    """Get daily usage breakdown."""
    service = get_analytics_service()
    return service.get_daily_usage(user["id"], days)


@router.get("/monthly-entries")
async def get_monthly_entries(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict:
    """Get total entries created this month."""
    service = get_analytics_service()
    count = service.get_monthly_entries(user["id"])
    return {"month_entries": count}


@router.get("/chains/{chain_id}/activity")
async def get_chain_activity(
    chain_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> list[dict]:
    """Get recent activity for a specific chain."""
    service = get_analytics_service()
    return service.get_chain_activity(user["id"], chain_id, limit)


@router.get("/top-chains")
async def get_top_chains(
    limit: int = Query(default=10, ge=1, le=50),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> list[dict]:
    """Get most active chains."""
    service = get_analytics_service()
    return service.get_top_chains(user["id"], limit)


@router.get("/hourly-distribution")
async def get_hourly_distribution(
    days: int = Query(default=7, ge=1, le=90),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
) -> dict[int, int]:
    """Get hourly distribution of API calls."""
    service = get_analytics_service()
    return service.get_hourly_distribution(user["id"], days)
