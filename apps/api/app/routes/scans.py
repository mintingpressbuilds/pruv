"""Scan routes — upload chain JSON or scan by chain ID."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import ScanResponse
from ..services.scan_service import scan_service

router = APIRouter(prefix="/v1/scans", tags=["scans"])

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("", response_model=ScanResponse)
async def trigger_scan(
    file: UploadFile | None = File(default=None),
    chain_id: str | None = Form(default=None),
    options: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Trigger a scan via file upload or chain ID."""
    parsed_options: dict[str, Any] | None = None
    if options:
        try:
            parsed_options = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid options JSON")

    if file:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 10 MB)")
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        return scan_service.scan_file(
            file_content=content,
            chain_id=chain_id,
            options=parsed_options,
        )

    if chain_id:
        return scan_service.scan_chain_id(
            chain_id=chain_id,
            user_id=user["id"],
            options=parsed_options,
        )

    raise HTTPException(
        status_code=400,
        detail="Provide either a file upload or a chain_id to scan",
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get the status/result of a previous scan."""
    result = scan_service.get_scan(scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result
