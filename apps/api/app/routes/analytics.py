"""Analytics routes for the pruv API."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.analytics_service import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/usage")
async def get_usage_summary(
    user_id: str = "demo_user",
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    """Get usage summary for the current user."""
    service = get_analytics_service()
    return service.get_usage_summary(user_id, days)


@router.get("/daily")
async def get_daily_usage(
    user_id: str = "demo_user",
    days: int = Query(default=30, ge=1, le=365),
) -> list[dict]:
    """Get daily usage breakdown."""
    service = get_analytics_service()
    return service.get_daily_usage(user_id, days)


@router.get("/monthly-entries")
async def get_monthly_entries(
    user_id: str = "demo_user",
) -> dict:
    """Get total entries created this month."""
    service = get_analytics_service()
    count = service.get_monthly_entries(user_id)
    return {"month_entries": count}


@router.get("/chains/{chain_id}/activity")
async def get_chain_activity(
    chain_id: str,
    user_id: str = "demo_user",
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    """Get recent activity for a specific chain."""
    service = get_analytics_service()
    return service.get_chain_activity(user_id, chain_id, limit)


@router.get("/top-chains")
async def get_top_chains(
    user_id: str = "demo_user",
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    """Get most active chains."""
    service = get_analytics_service()
    return service.get_top_chains(user_id, limit)


@router.get("/hourly-distribution")
async def get_hourly_distribution(
    user_id: str = "demo_user",
    days: int = Query(default=7, ge=1, le=90),
) -> dict[int, int]:
    """Get hourly distribution of API calls."""
    service = get_analytics_service()
    return service.get_hourly_distribution(user_id, days)
