"""Dashboard routes — aggregated stats for the dashboard UI."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import DashboardStatsResponse
from ..services.chain_service import chain_service
from ..services.receipt_service import receipt_service

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get aggregated dashboard statistics."""
    user_id = user["id"]
    user_chains = chain_service.list_chains(user_id)
    total_chains = len(user_chains)
    total_entries = chain_service.get_entry_count(user_id)
    total_receipts = receipt_service.get_receipt_count(user_id)

    # Calculate verified percentage
    verified_count = 0
    for c in user_chains:
        result = chain_service.verify_chain(c["id"])
        if result["valid"]:
            verified_count += 1
    verified_percentage = (
        round((verified_count / total_chains) * 100, 1) if total_chains > 0 else 100.0
    )

    # Build recent activity from chains and entries
    activity: list[dict[str, Any]] = []
    for c in user_chains:
        activity.append({
            "id": uuid.uuid4().hex[:12],
            "type": "chain_created",
            "description": f"created chain \"{c['name']}\"",
            "timestamp": c["created_at"],
            "chain_id": c["id"],
            "chain_name": c["name"],
            "actor": user_id,
        })
        entries = chain_service.list_entries(c["id"], limit=5)
        for e in entries:
            activity.append({
                "id": uuid.uuid4().hex[:12],
                "type": "entry_added",
                "description": f"added entry #{e['index']}: {e['operation']}",
                "timestamp": e["timestamp"],
                "chain_id": c["id"],
                "chain_name": c["name"],
                "actor": user_id,
            })

    # Sort by timestamp descending and take top 20
    activity.sort(key=lambda a: a["timestamp"], reverse=True)
    activity = activity[:20]

    return {
        "total_chains": total_chains,
        "total_entries": total_entries,
        "total_receipts": total_receipts,
        "verified_percentage": verified_percentage,
        "recent_activity": activity,
    }
