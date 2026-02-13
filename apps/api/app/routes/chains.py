"""Chain and entry routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import (
    ChainCreate,
    ChainListResponse,
    ChainResponse,
    ChainShareResponse,
    ChainVerifyResponse,
    EntryBatchCreate,
    EntryCreate,
    EntryListResponse,
    EntryResponse,
)
from ..services.chain_service import chain_service

router = APIRouter(prefix="/v1/chains", tags=["chains"])


@router.post("", response_model=ChainResponse)
async def create_chain(
    body: ChainCreate,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Create a new chain."""
    chain = chain_service.create_chain(
        user_id=user["id"],
        name=body.name,
        auto_redact=body.auto_redact,
    )
    return chain


@router.get("", response_model=ChainListResponse)
async def list_chains(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """List all chains for the current user."""
    chains = chain_service.list_chains(user["id"])
    return {"chains": chains, "total": len(chains)}


@router.get("/{chain_id}", response_model=ChainResponse)
async def get_chain(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get a chain by ID."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    return chain


@router.get("/{chain_id}/verify", response_model=ChainVerifyResponse)
async def verify_chain(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Verify a chain's integrity."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    result = chain_service.verify_chain(chain_id)
    return result


@router.get("/{chain_id}/share", response_model=ChainShareResponse)
async def share_chain(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get a shareable link for a chain."""
    result = chain_service.create_share_link(chain_id, user["id"])
    if not result:
        raise HTTPException(status_code=404, detail="Chain not found")
    return result


# ──── Entries ────


@router.post("/{chain_id}/entries", response_model=EntryResponse)
async def append_entry(
    chain_id: str,
    body: EntryCreate,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Append an entry to a chain."""
    entry = chain_service.append_entry(
        chain_id=chain_id,
        user_id=user["id"],
        operation=body.operation,
        x_state=body.x_state,
        y_state=body.y_state,
        status=body.status,
        metadata=body.metadata,
        signature=body.signature,
        signer_id=body.signer_id,
        public_key=body.public_key,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Chain not found")
    return entry


@router.post("/{chain_id}/entries/batch", response_model=EntryListResponse)
async def batch_append_entries(
    chain_id: str,
    body: EntryBatchCreate,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Batch append entries to a chain."""
    entries_data = [e.model_dump() for e in body.entries]
    entries = chain_service.batch_append(chain_id, user["id"], entries_data)
    if not entries:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"entries": entries, "total": len(entries)}


@router.get("/{chain_id}/entries", response_model=EntryListResponse)
async def list_entries(
    chain_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """List entries in a chain."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    entries = chain_service.list_entries(chain_id, offset, limit)
    return {"entries": entries, "total": len(entries)}
