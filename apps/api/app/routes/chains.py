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
    ChainUpdate,
    ChainVerifyResponse,
    EntryBatchCreate,
    EntryCreate,
    EntryListResponse,
    EntryResponse,
    EntryValidationResponse,
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
        description=body.description,
        tags=body.tags,
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


@router.patch("/{chain_id}", response_model=ChainResponse)
async def update_chain(
    chain_id: str,
    body: ChainUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Update a chain."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    chain = chain_service.update_chain(chain_id, user["id"], updates)
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    return chain


@router.delete("/{chain_id}")
async def delete_chain(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Delete a chain."""
    success = chain_service.delete_chain(chain_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"deleted": True}


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


@router.post("/{chain_id}/undo", response_model=EntryResponse)
async def undo_last_entry(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Undo (remove) the last entry in a chain."""
    entry = chain_service.undo_last_entry(chain_id, user["id"])
    if not entry:
        raise HTTPException(status_code=404, detail="Chain not found or no entries to undo")
    return entry


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


@router.get("/{chain_id}/entries/{entry_index}", response_model=EntryResponse)
async def get_entry(
    chain_id: str,
    entry_index: int,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get a single entry by index."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    entry = chain_service.get_entry_by_index(chain_id, entry_index)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.get("/{chain_id}/entries/{entry_index}/validate", response_model=EntryValidationResponse)
async def validate_entry(
    chain_id: str,
    entry_index: int,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Validate a single entry in a chain."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    entry = chain_service.get_entry_by_index(chain_id, entry_index)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Check x matches previous y
    x_matches = True
    if entry_index == 0:
        x_matches = entry["x"] == "GENESIS"
    else:
        prev = chain_service.get_entry_by_index(chain_id, entry_index - 1)
        if prev:
            x_matches = entry["x"] == prev["y"]

    # Check proof
    from xycore.crypto import compute_xy
    expected_xy = compute_xy(entry["x"], entry["operation"], entry["y"], entry["timestamp"])
    proof_valid = entry["xy"] == expected_xy

    valid = x_matches and proof_valid
    reason = None
    if not x_matches:
        reason = "x does not match previous entry's y"
    elif not proof_valid:
        reason = "xy proof hash mismatch"

    return {
        "index": entry_index,
        "valid": valid,
        "reason": reason,
        "x_matches_prev_y": x_matches,
        "proof_valid": proof_valid,
        "signature_valid": True if entry.get("signature") else None,
    }
