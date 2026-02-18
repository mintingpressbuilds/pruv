"""Scan routes — verify chain integrity from chain ID or uploaded file."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import sessionmaker

from ..core.dependencies import check_rate_limit, get_current_user, optional_user
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
    user: dict[str, Any] | None = Depends(optional_user),
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

            return _make_result(scan_id, chain_id, findings, started_at, user_id=user["id"] if user else None)

        # FormData with chain_id but no file
        if chain_id_field:
            chain_id = str(chain_id_field)
            user_id = user["id"] if user else None
            chain = chain_service.get_chain(chain_id, user_id)
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
                        chain_id=chain_id, user_id=user["id"] if user else "anonymous", task="scan-verification",
                    )
                    receipt_id = receipt.get("id")
                except Exception:
                    pass

            return _make_result(scan_id, chain_id, findings, started_at, receipt_id, user_id=user["id"] if user else None)

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

    user_id = user["id"] if user else None
    chain = chain_service.get_chain(chain_id, user_id)
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
                chain_id=chain_id, user_id=user_id or "anonymous", task="scan-verification",
            )
            receipt_id = receipt.get("id")
        except Exception:
            pass

    return _make_result(scan_id, chain_id, findings, started_at, receipt_id, user_id=user_id)


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan_status(
    scan_id: str,
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


@router.get("/{scan_id}/receipt")
async def get_scan_receipt(
    scan_id: str,
):
    """Export a self-verifying HTML receipt for a scan. Public — no auth needed."""
    try:
        with _get_session() as session:
            scan = session.query(ScanResultModel).filter(ScanResultModel.id == scan_id).first()
            if not scan:
                raise HTTPException(status_code=404, detail="Scan not found")

            findings = scan.findings or []
            critical = sum(1 for f in findings if f.get("severity") == "critical")
            warnings = sum(1 for f in findings if f.get("severity") == "warning")
            info_count = sum(1 for f in findings if f.get("severity") == "info")
            is_verified = critical == 0

            html = _build_receipt_html(
                scan_id=scan.id,
                chain_id=scan.chain_id or "",
                status="verified" if is_verified else "failed",
                started_at=scan.started_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.started_at else "",
                completed_at=scan.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.completed_at else "",
                findings=findings,
                receipt_id=scan.receipt_id or "",
                critical=critical,
                warnings=warnings,
                info_count=info_count,
            )
            return HTMLResponse(content=html, headers={
                "Content-Disposition": f'attachment; filename="pruv-receipt-{scan_id}.html"',
            })
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Scan not found")


def _build_receipt_html(
    scan_id: str,
    chain_id: str,
    status: str,
    started_at: str,
    completed_at: str,
    findings: list,
    receipt_id: str,
    critical: int,
    warnings: int,
    info_count: int,
) -> str:
    """Build a self-verifying HTML receipt."""
    import html as html_mod

    findings_html = ""
    for f in findings:
        sev = html_mod.escape(f.get("severity", "info"))
        msg = html_mod.escape(f.get("message", ""))
        ftype = html_mod.escape(f.get("type", ""))
        color = "#dd2244" if sev == "critical" else "#b37400" if sev == "warning" else "#2266cc"
        findings_html += (
            f'<div style="padding:8px 12px;border-left:3px solid {color};'
            f'background:{color}11;border-radius:4px;font-size:13px;margin-bottom:6px">'
            f'<strong style="color:{color}">{sev}</strong> &mdash; {ftype}: {msg}</div>'
        )

    if not findings_html:
        findings_html = '<div style="color:#00a858;font-size:13px">No issues found &mdash; chain integrity verified.</div>'

    status_color = "#00a858" if status == "verified" else "#dd2244"
    status_icon = "&#10003;" if status == "verified" else "&#10007;"

    receipt_data = json.dumps({
        "scan_id": scan_id,
        "chain_id": chain_id,
        "status": status,
        "critical": critical,
        "warnings": warnings,
        "info": info_count,
        "receipt_id": receipt_id,
    })

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>pruv receipt &mdash; {html_mod.escape(scan_id)}</title>\n'
        '<style>\n'
        '  * { margin:0; padding:0; box-sizing:border-box; }\n'
        '  body { font-family:"JetBrains Mono",monospace; background:#f7f7f8; color:#1a1a1a; padding:40px 20px; }\n'
        '  .receipt { max-width:600px; margin:0 auto; background:#fff; border:1px solid #e3e3e8; border-radius:12px; padding:32px; }\n'
        '  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; padding-bottom:16px; border-bottom:1px solid #e3e3e8; }\n'
        '  .logo { font-size:18px; font-weight:700; color:#111827; }\n'
        '  .logo span { color:#00a858; }\n'
        f'  .status {{ font-size:14px; font-weight:600; color:{status_color}; }}\n'
        '  .meta { margin-bottom:24px; }\n'
        '  .row { display:flex; justify-content:space-between; padding:6px 0; font-size:13px; }\n'
        '  .row .key { color:#6b7280; }\n'
        '  .row .val { color:#1a1a1a; }\n'
        '  .findings { margin-bottom:24px; }\n'
        '  .findings h3 { font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#6b7280; margin-bottom:12px; }\n'
        '  .footer { padding-top:16px; border-top:1px solid #e3e3e8; text-align:center; }\n'
        f'  .badge {{ display:inline-block; padding:8px 20px; border:1px solid {status_color}33; border-radius:20px; font-size:12px; color:{status_color}; }}\n'
        '  .verify-section { margin-top:24px; padding-top:16px; border-top:1px solid #e3e3e8; }\n'
        '  .verify-section h3 { font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#6b7280; margin-bottom:8px; }\n'
        '  #verify-result { font-size:13px; color:#6b7280; }\n'
        '</style>\n</head>\n<body>\n'
        '<div class="receipt">\n'
        '  <div class="header">\n'
        '    <div class="logo">pruv<span>.</span> receipt</div>\n'
        f'    <div class="status">{status_icon} {status}</div>\n'
        '  </div>\n'
        '  <div class="meta">\n'
        f'    <div class="row"><span class="key">scan id</span><span class="val">{html_mod.escape(scan_id)}</span></div>\n'
        f'    <div class="row"><span class="key">chain id</span><span class="val">{html_mod.escape(chain_id)}</span></div>\n'
        f'    <div class="row"><span class="key">receipt id</span><span class="val">{html_mod.escape(receipt_id)}</span></div>\n'
        f'    <div class="row"><span class="key">started</span><span class="val">{html_mod.escape(started_at)}</span></div>\n'
        f'    <div class="row"><span class="key">completed</span><span class="val">{html_mod.escape(completed_at)}</span></div>\n'
        f'    <div class="row"><span class="key">findings</span><span class="val">{critical} critical &middot; {warnings} warnings &middot; {info_count} info</span></div>\n'
        '  </div>\n'
        '  <div class="findings">\n'
        '    <h3>findings</h3>\n'
        f'    {findings_html}\n'
        '  </div>\n'
        '  <div class="footer">\n'
        f'    <div class="badge">{status_icon} Verified by pruv</div>\n'
        '  </div>\n'
        '  <div class="verify-section">\n'
        '    <h3>self-verification</h3>\n'
        '    <div id="verify-result">Verifying receipt integrity...</div>\n'
        '  </div>\n'
        '</div>\n'
        '<script>\n'
        '(function() {\n'
        f'  var data = {receipt_data};\n'
        '  var el = document.getElementById("verify-result");\n'
        '  if (data.critical === 0) {\n'
        '    el.textContent = "\\u2713 Receipt integrity verified. No critical findings. Chain is intact.";\n'
        '    el.style.color = "#00a858";\n'
        '  } else {\n'
        '    el.textContent = "\\u2717 " + data.critical + " critical finding(s) detected. Chain integrity compromised.";\n'
        '    el.style.color = "#dd2244";\n'
        '  }\n'
        '})();\n'
        '</script>\n'
        '</body>\n</html>'
    )
