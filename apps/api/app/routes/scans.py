"""Scan routes — verify chain integrity from chain ID or uploaded file."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import sessionmaker

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..models.database import ScanResult as ScanResultModel, get_engine
from ..services.chain_service import chain_service

logger = logging.getLogger("pruv.api.scans")

router = APIRouter(prefix="/v1/scans", tags=["scans"])


# ──── Schemas ────


class ScanFindingResponse(BaseModel):
    severity: str
    type: str
    message: str
    entry_index: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ScanResponse(BaseModel):
    id: str
    status: str
    chain_id: str | None = None
    started_at: str
    completed_at: str | None = None
    findings: list[ScanFindingResponse] = Field(default_factory=list)
    receipt_id: str | None = None


# ──── Database session ────

_session_factory: sessionmaker | None = None


def _get_session():
    global _session_factory
    if _session_factory is None:
        from ..core.config import settings
        if settings.database_url:
            engine = get_engine(settings.database_url)
            _session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )
    if _session_factory is None:
        raise RuntimeError("Database not initialized for scans")
    return _session_factory()


# ──── Helpers ────


def _verify_entries(
    entries: list[dict[str, Any]],
    deep_verify: bool = True,
    check_signatures: bool = False,
) -> list[dict[str, Any]]:
    """Walk entries and produce findings."""
    from xycore.crypto import compute_xy

    findings: list[dict[str, Any]] = []

    for i, entry in enumerate(entries):
        x = entry.get("x", "")
        y = entry.get("y", "")
        xy = entry.get("xy", entry.get("xy_proof", ""))
        operation = entry.get("operation", entry.get("action", ""))
        timestamp = entry.get("timestamp", 0)

        # Chain rule
        if i == 0:
            if x != "GENESIS":
                findings.append({
                    "severity": "critical",
                    "type": "chain_rule_violation",
                    "message": f"First entry x is '{x}', expected 'GENESIS'",
                    "entry_index": i,
                })
        else:
            prev_y = entries[i - 1].get("y", "")
            if x != prev_y:
                findings.append({
                    "severity": "critical",
                    "type": "chain_break",
                    "message": f"Entry #{i} x does not match previous entry y — chain is broken",
                    "entry_index": i,
                })

        # Proof verification
        if deep_verify and xy and operation:
            expected_xy = compute_xy(x, operation, y, timestamp)
            if xy != expected_xy:
                findings.append({
                    "severity": "critical",
                    "type": "proof_mismatch",
                    "message": f"Entry #{i} xy proof does not match recomputed hash",
                    "entry_index": i,
                })

        # Signature verification
        if check_signatures:
            sig = entry.get("signature")
            pub_key = entry.get("public_key")

            if sig and pub_key:
                try:
                    from xycore import XYEntry as XYE
                    from xycore.signature import verify_signature

                    xy_entry = XYE(
                        index=entry.get("index", i),
                        timestamp=timestamp,
                        operation=operation,
                        x=x,
                        y=y,
                        xy=xy,
                        status=entry.get("status", "success"),
                    )
                    xy_entry.signature = sig
                    xy_entry.public_key = pub_key
                    xy_entry.signer_id = entry.get("signer_id")

                    if not verify_signature(xy_entry):
                        findings.append({
                            "severity": "critical",
                            "type": "signature_invalid",
                            "message": f"Entry #{i} has an invalid Ed25519 signature",
                            "entry_index": i,
                        })
                except ImportError:
                    findings.append({
                        "severity": "warning",
                        "type": "signature_check_unavailable",
                        "message": f"Entry #{i} has a signature but Ed25519 library is not installed",
                        "entry_index": i,
                    })
            elif sig and not pub_key:
                findings.append({
                    "severity": "warning",
                    "type": "signature_missing_key",
                    "message": f"Entry #{i} has a signature but no public key",
                    "entry_index": i,
                })

    return findings


def _make_result(
    scan_id: str,
    chain_id: str | None,
    findings: list[dict[str, Any]],
    started_at: float,
    receipt_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    completed_at = time.time()
    started_dt = datetime.fromtimestamp(started_at, tz=timezone.utc)
    completed_dt = datetime.fromtimestamp(completed_at, tz=timezone.utc)

    result = {
        "id": scan_id,
        "status": "completed",
        "chain_id": chain_id,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at)),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(completed_at)),
        "findings": findings,
        "receipt_id": receipt_id,
    }

    # Persist to database
    try:
        with _get_session() as session:
            scan_row = ScanResultModel(
                id=scan_id,
                user_id=user_id,
                status="completed",
                chain_id=chain_id,
                started_at=started_dt,
                completed_at=completed_dt,
                findings=findings,
                receipt_id=receipt_id,
            )
            session.add(scan_row)
            session.commit()
    except Exception:
        logger.exception("Failed to persist scan result %s", scan_id)

    return result


# ──── Routes ────


@router.post("", response_model=ScanResponse)
async def trigger_scan(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Trigger a scan by chain ID or uploaded file.

    Accepts either:
    - JSON body: ``{"chain_id": "...", "options": {...}}``
    - FormData: file upload with optional chain_id and options fields
    """
    scan_id = uuid.uuid4().hex[:12]
    started_at = time.time()
    content_type = request.headers.get("content-type", "")

    # ── FormData path (file upload) ──
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        chain_id_field = form.get("chain_id")
        options_field = form.get("options")

        deep_verify = True
        check_signatures = True
        generate_receipt = True
        if options_field:
            try:
                opts = json.loads(str(options_field))
                deep_verify = opts.get("deep_verify", True)
                check_signatures = opts.get("check_signatures", True)
                generate_receipt = opts.get("generate_receipt", True)
            except (json.JSONDecodeError, TypeError):
                pass

        if file:
            content = await file.read()
            try:
                file_data = json.loads(content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise HTTPException(status_code=400, detail="Invalid JSON file")

            chain_id = file_data.get("chain_id", file_data.get("id", "uploaded"))
            entries = file_data.get("entries", [])

            if not entries:
                findings = [{
                    "severity": "info",
                    "type": "empty_chain",
                    "message": "No entries found in uploaded file",
                }]
            else:
                findings = _verify_entries(
                    entries,
                    deep_verify=deep_verify,
                    check_signatures=check_signatures,
                )

            return _make_result(scan_id, chain_id, findings, started_at, user_id=user["id"])

        # FormData with chain_id but no file
        if chain_id_field:
            chain_id = str(chain_id_field)
            chain = chain_service.get_chain(chain_id, user["id"])
            if not chain:
                raise HTTPException(status_code=404, detail="Chain not found")

            entries = chain_service.list_entries(chain_id, offset=0, limit=10000)
            findings = _verify_entries(
                entries,
                deep_verify=deep_verify,
                check_signatures=check_signatures,
            )

            receipt_id = None
            if generate_receipt and len(entries) > 0:
                try:
                    from ..services.receipt_service import receipt_service
                    receipt = receipt_service.create_receipt(
                        chain_id=chain_id, user_id=user["id"], task="scan-verification",
                    )
                    receipt_id = receipt.get("id")
                except Exception:
                    pass

            return _make_result(scan_id, chain_id, findings, started_at, receipt_id, user_id=user["id"])

        raise HTTPException(status_code=400, detail="Provide chain_id or upload a file")

    # ── JSON body path ──
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    chain_id = body.get("chain_id")
    if not chain_id:
        raise HTTPException(status_code=400, detail="Provide chain_id or upload a file")

    opts = body.get("options", {})
    deep_verify = opts.get("deep_verify", True)
    check_signatures = opts.get("check_signatures", True)
    generate_receipt = opts.get("generate_receipt", True)

    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    entries = chain_service.list_entries(chain_id, offset=0, limit=10000)
    findings = _verify_entries(
        entries,
        deep_verify=deep_verify,
        check_signatures=check_signatures,
    )

    receipt_id = None
    if generate_receipt and len(entries) > 0:
        try:
            from ..services.receipt_service import receipt_service
            receipt = receipt_service.create_receipt(
                chain_id=chain_id, user_id=user["id"], task="scan-verification",
            )
            receipt_id = receipt.get("id")
        except Exception:
            pass

    return _make_result(scan_id, chain_id, findings, started_at, receipt_id, user_id=user["id"])


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan_status(
    scan_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get the status and results of a scan."""
    try:
        with _get_session() as session:
            scan = session.query(ScanResultModel).filter(ScanResultModel.id == scan_id).first()
            if not scan:
                raise HTTPException(status_code=404, detail="Scan not found")
            return {
                "id": scan.id,
                "status": scan.status,
                "chain_id": scan.chain_id,
                "started_at": scan.started_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.started_at else None,
                "completed_at": scan.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.completed_at else None,
                "findings": scan.findings or [],
                "receipt_id": scan.receipt_id,
            }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Scan not found")
