"""Verification and shared chain routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import CertificateResponse, SharedChainResponse
from ..services.chain_service import chain_service

router = APIRouter(tags=["verification"])


@router.get("/v1/certificate/{chain_id}", response_model=CertificateResponse)
async def get_certificate(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get a verification certificate for a chain."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    verification = chain_service.verify_chain(chain_id)
    return {
        "chain_id": chain_id,
        "chain_name": chain["name"],
        "valid": verification["valid"],
        "length": verification["length"],
        "root_xy": chain.get("root_xy"),
        "head_xy": chain.get("head_xy"),
        "verified_at": datetime.now(timezone.utc),
        "break_index": verification.get("break_index"),
    }


@router.get("/v1/shared/{share_id}", response_model=SharedChainResponse)
async def get_shared_chain(share_id: str):
    """Get a publicly shared chain. Intentionally public."""
    result = chain_service.get_shared_chain(share_id)
    if not result:
        raise HTTPException(status_code=404, detail="Shared chain not found")

    chain, entries = result
    verification = chain_service.verify_chain(chain["id"])

    return {
        "chain": chain,
        "entries": entries,
        "verified": verification["valid"],
    }
