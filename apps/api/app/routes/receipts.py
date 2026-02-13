"""Receipt routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import ReceiptResponse
from ..services.receipt_service import receipt_service

router = APIRouter(prefix="/v1/receipts", tags=["receipts"])


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get a receipt by ID."""
    receipt = receipt_service.get_receipt_for_user(receipt_id, user["id"])
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.get("/{receipt_id}/pdf")
async def get_receipt_pdf(
    receipt_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Export a receipt as PDF data."""
    receipt = receipt_service.get_receipt_for_user(receipt_id, user["id"])
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt_service.get_receipt_pdf_data(receipt_id)


@router.get("/{receipt_id}/badge")
async def get_receipt_badge(
    receipt_id: str,
):
    """Get an embeddable SVG badge for a receipt. Public endpoint."""
    badge = receipt_service.get_receipt_badge(receipt_id)
    if not badge:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return Response(
        content=badge["svg"],
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=300"},
    )
