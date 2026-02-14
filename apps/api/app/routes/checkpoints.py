"""Checkpoint routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import (
    CheckpointCreate,
    CheckpointListResponse,
    CheckpointPreviewResponse,
    CheckpointResponse,
    CheckpointRestoreResponse,
)
from ..services.checkpoint_service import checkpoint_service

router = APIRouter(prefix="/v1/chains/{chain_id}/checkpoints", tags=["checkpoints"])


@router.post("", response_model=CheckpointResponse)
async def create_checkpoint(
    chain_id: str,
    body: CheckpointCreate,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Create a checkpoint."""
    cp = checkpoint_service.create_checkpoint(chain_id, user["id"], body.name)
    if not cp:
        raise HTTPException(status_code=404, detail="Chain not found")
    return cp


@router.get("", response_model=CheckpointListResponse)
async def list_checkpoints(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """List checkpoints for a chain."""
    checkpoints = checkpoint_service.list_checkpoints(chain_id)
    return {"checkpoints": checkpoints}


@router.get("/{checkpoint_id}/preview", response_model=CheckpointPreviewResponse)
async def preview_restore(
    chain_id: str,
    checkpoint_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Preview what will change if restoring to a checkpoint."""
    result = checkpoint_service.preview_restore(chain_id, checkpoint_id, user["id"])
    if not result:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return result


@router.post("/{checkpoint_id}/restore", response_model=CheckpointRestoreResponse)
async def restore_checkpoint(
    chain_id: str,
    checkpoint_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Restore a chain to a checkpoint."""
    result = checkpoint_service.restore_checkpoint(chain_id, checkpoint_id, user["id"])
    if not result:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return result
