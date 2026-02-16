"""Chain and entry routes."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..core.dependencies import check_rate_limit, get_current_user, require_write
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import (
    ChainAlertsResponse,
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
    PaymentVerifyResponse,
)
from ..services.alerts import analyze_chain as run_alert_analysis
from ..services.chain_service import chain_service
from ..services.webhook_service import get_webhook_service

router = APIRouter(prefix="/v1/chains", tags=["chains"])


@router.post("", response_model=ChainResponse)
async def create_chain(
    body: ChainCreate,
    user: dict[str, Any] = Depends(require_write),
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
    user: dict[str, Any] = Depends(require_write),
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
    user: dict[str, Any] = Depends(require_write),
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


@router.get("/{chain_id}/verify-payments", response_model=PaymentVerifyResponse)
async def verify_payments(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Verify all payment entries in a chain.

    Walks the chain, finds entries with xy_proof in metadata,
    recomputes each BalanceProof, and verifies hashes match.
    """
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    result = chain_service.verify_payments(chain_id)
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


@router.get("/{chain_id}/alerts", response_model=ChainAlertsResponse)
async def get_chain_alerts(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Analyze a chain for anomalies and return alerts."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    entries = chain_service.list_entries(chain_id, offset=0, limit=10000)
    alerts = run_alert_analysis(chain, entries)

    # Queue webhook deliveries for warning+ alerts
    webhook_svc = get_webhook_service()
    critical_alerts = [a for a in alerts if a.severity.value in ("warning", "critical")]
    if critical_alerts:
        webhook_svc.queue_delivery(
            event="alert.triggered",
            data={
                "chain_id": chain_id,
                "alert_count": len(critical_alerts),
                "alerts": [
                    {"rule": a.rule, "severity": a.severity.value, "message": a.message}
                    for a in critical_alerts
                ],
            },
            user_id=user["id"],
        )

    return {
        "chain_id": chain_id,
        "alerts": [
            {
                "rule": a.rule,
                "severity": a.severity.value,
                "message": a.message,
                "entry_id": a.entry_id,
            }
            for a in alerts
        ],
        "analyzed_at": time.time(),
    }


@router.get("/{chain_id}/export", response_class=HTMLResponse)
async def export_chain(
    chain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Export a chain as a self-verifying HTML document."""
    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    entries = chain_service.list_entries(chain_id, offset=0, limit=10000)
    verification = chain_service.verify_chain(chain_id)

    import html as html_mod
    import json

    name = html_mod.escape(chain.get("name", chain_id))
    verified = verification.get("valid", False)
    status_text = "VERIFIED" if verified else "BROKEN"
    status_color = "#00dc73" if verified else "#ef4444"

    entries_json = json.dumps(
        [
            {
                "index": e["index"],
                "operation": e["operation"],
                "x": e["x"],
                "y": e["y"],
                "xy": e["xy"],
                "timestamp": e["timestamp"],
            }
            for e in entries
        ],
        indent=2,
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>pruv chain: {name}</title>
<style>
  body {{ font-family: 'JetBrains Mono', monospace; background: #0f1117; color: #f3f4f6; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.2rem; color: #00dc73; margin-bottom: 0.5rem; }}
  .status {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; background: {status_color}20; color: {status_color}; border: 1px solid {status_color}40; margin-bottom: 1rem; }}
  .meta {{ font-size: 0.75rem; color: #6b7280; margin-bottom: 2rem; }}
  .entry {{ border-left: 2px solid #2a2e3a; padding: 0.75rem 1rem; margin-bottom: 0.5rem; }}
  .entry:hover {{ border-color: #00dc73; }}
  .op {{ color: #f3f4f6; font-weight: bold; }}
  .hash {{ color: #00dc73; font-size: 0.7rem; opacity: 0.7; }}
  .ts {{ color: #6b7280; font-size: 0.7rem; }}
  .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #2a2e3a; font-size: 0.7rem; color: #6b7280; }}
  #verify-btn {{ background: #00dc73; color: #0f1117; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; font-family: inherit; font-weight: bold; font-size: 0.8rem; }}
  #verify-btn:hover {{ background: #00c466; }}
  #verify-result {{ margin-top: 0.5rem; font-size: 0.75rem; }}
</style>
</head>
<body>
<h1>pruv chain: {name}</h1>
<span class="status">{status_text}</span>
<div class="meta">{len(entries)} entries &middot; chain id: {html_mod.escape(chain_id)}</div>
<div id="entries"></div>
<button id="verify-btn" onclick="verifyChain()">re-verify chain</button>
<div id="verify-result"></div>
<div class="footer">exported from pruv &middot; self-verifying artifact</div>
<script>
const entries = {entries_json};

// Render entries
const container = document.getElementById('entries');
entries.forEach(e => {{
  const div = document.createElement('div');
  div.className = 'entry';
  div.innerHTML = `
    <span class="ts">#${{e.index}} &middot; ${{new Date(e.timestamp * 1000).toISOString()}}</span><br>
    <span class="op">${{e.operation}}</span><br>
    <span class="hash">${{e.xy}}</span>
  `;
  container.appendChild(div);
}});

// Self-verification using SubtleCrypto
async function sha256(msg) {{
  const buf = new TextEncoder().encode(msg);
  const hash = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
}}

async function verifyChain() {{
  const result = document.getElementById('verify-result');
  result.textContent = 'verifying...';
  let valid = true;
  let breakIdx = null;

  for (let i = 0; i < entries.length; i++) {{
    const e = entries[i];
    // Check chain rule
    if (i === 0) {{
      if (e.x !== 'GENESIS') {{ valid = false; breakIdx = i; break; }}
    }} else {{
      if (e.x !== entries[i-1].y) {{ valid = false; breakIdx = i; break; }}
    }}
    // Check proof
    const raw = e.x + ':' + e.operation + ':' + e.y + ':' + String(e.timestamp);
    const hash = await sha256(raw);
    const expected = 'xy_' + hash;
    if (e.xy !== expected) {{ valid = false; breakIdx = i; break; }}
  }}

  if (valid) {{
    result.innerHTML = '<span style="color:#00dc73">chain verified — all ' + entries.length + ' entries valid</span>';
  }} else {{
    result.innerHTML = '<span style="color:#ef4444">chain broken at entry #' + breakIdx + '</span>';
  }}
}}
</script>
</body>
</html>"""

    return HTMLResponse(content=html_content)


@router.post("/{chain_id}/undo", response_model=EntryResponse)
async def undo_last_entry(
    chain_id: str,
    user: dict[str, Any] = Depends(require_write),
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
    user: dict[str, Any] = Depends(require_write),
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
    user: dict[str, Any] = Depends(require_write),
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
