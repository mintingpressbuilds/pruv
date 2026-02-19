"""Provenance routes — artifact origin, transitions, and verification."""

from __future__ import annotations

import html as html_mod
import json
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..core.dependencies import check_rate_limit, get_current_user, require_write
from ..core.rate_limit import RateLimitResult
from ..schemas.schemas import (
    ArtifactListResponse,
    ArtifactResponse,
    ProvenanceOriginRequest,
    ProvenanceTransitionRequest,
    ProvenanceVerifyResponse,
)
from ..services.provenance_service import provenance_service

router = APIRouter(prefix="/v1/provenance", tags=["provenance"])


@router.post("/origin", response_model=ArtifactResponse)
async def register_origin(
    body: ProvenanceOriginRequest,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Register a new artifact's origin.

    Only the content hash is stored — actual content never leaves the owner.
    """
    artifact = provenance_service.register_origin(
        user_id=user["id"],
        content_hash=body.content_hash,
        name=body.name,
        creator=body.creator,
        content_type=body.content_type,
        metadata=body.metadata,
    )
    return artifact


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """List all artifacts for the current user."""
    artifacts = provenance_service.list_artifacts(user["id"])
    return {"artifacts": artifacts, "total": len(artifacts)}


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get an artifact by its pa_ address."""
    artifact = provenance_service.get_artifact(artifact_id, user["id"])
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.post("/{artifact_id}/transition")
async def record_transition(
    artifact_id: str,
    body: ProvenanceTransitionRequest,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Record a modification to an artifact.

    Appends a transition entry with previous_hash -> new_hash.
    """
    entry = provenance_service.transition(
        artifact_id=artifact_id,
        user_id=user["id"],
        new_hash=body.new_hash,
        modifier=body.modifier,
        reason=body.reason,
        metadata=body.metadata,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return entry


@router.get("/{artifact_id}/verify", response_model=ProvenanceVerifyResponse)
async def verify_provenance(
    artifact_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Verify an artifact's provenance chain."""
    result = provenance_service.verify(artifact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return result


@router.get("/{artifact_id}/history")
async def get_history(
    artifact_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get modification history for an artifact."""
    history = provenance_service.get_history(
        artifact_id, limit=limit, offset=offset
    )
    if history is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"entries": history, "total": len(history)}


@router.get("/{artifact_id}/receipt", response_class=HTMLResponse)
async def get_provenance_receipt(
    artifact_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Export provenance as a self-verifying HTML receipt.

    Shows: artifact name, type, creator, origin hash, modification
    timeline (who, when, why, hash before/after), current hash,
    verification status.
    """
    artifact = provenance_service.get_artifact(artifact_id, user["id"])
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    verification = provenance_service.verify(artifact_id)
    history = provenance_service.get_history(artifact_id, limit=100)

    name = html_mod.escape(artifact["name"])
    content_type = html_mod.escape(artifact.get("content_type", "unknown"))
    creator = html_mod.escape(artifact["creator"])
    origin_hash = html_mod.escape(artifact["content_hash"])
    current_hash = html_mod.escape(artifact["current_hash"])
    chain_id = html_mod.escape(artifact["chain_id"])

    verified = verification and verification.get("valid", False)
    status_text = "VERIFIED" if verified else "BROKEN"
    status_color = "#00dc73" if verified else "#ef4444"
    transition_count = verification.get("transition_count", 0) if verification else 0
    verify_message = html_mod.escape(
        verification.get("message", "") if verification else ""
    )

    # Build timeline entries from history (skip origin)
    timeline_entries = []
    for entry in (history or [])[1:]:
        y_state = entry.get("y_state") or {}
        timeline_entries.append(
            {
                "index": entry.get("index", 0),
                "operation": entry.get("operation", "unknown"),
                "timestamp": entry.get("timestamp", 0),
                "modifier": y_state.get("modifier", "unknown"),
                "reason": y_state.get("reason", ""),
                "previous_hash": (y_state.get("previous_hash", "") or "")[:12],
                "new_hash": (y_state.get("new_hash", "") or "")[:12],
            }
        )

    timeline_json = json.dumps(timeline_entries, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>pruv provenance: {name}</title>
<style>
  body {{ font-family: 'JetBrains Mono', monospace; background: #0f1117; color: #f3f4f6; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.2rem; color: #00dc73; margin-bottom: 0.5rem; }}
  .status {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; background: {status_color}20; color: {status_color}; border: 1px solid {status_color}40; margin-bottom: 1rem; }}
  .meta {{ font-size: 0.75rem; color: #6b7280; margin-bottom: 0.5rem; }}
  .meta strong {{ color: #f3f4f6; }}
  .section {{ margin: 1.5rem 0; }}
  .section-title {{ font-size: 0.85rem; color: #00dc73; margin-bottom: 0.5rem; font-weight: bold; }}
  .hash-block {{ background: #1a1d27; border: 1px solid #2a2e3a; border-radius: 0.5rem; padding: 0.75rem; font-size: 0.7rem; word-break: break-all; color: #9ca3af; }}
  .hash-label {{ font-size: 0.65rem; color: #6b7280; margin-bottom: 0.25rem; }}
  .transition {{ border-left: 2px solid #2a2e3a; padding: 0.5rem 1rem; margin-bottom: 0.25rem; }}
  .transition:hover {{ border-color: #00dc73; }}
  .modifier {{ color: #f3f4f6; font-weight: bold; font-size: 0.8rem; }}
  .reason {{ color: #9ca3af; font-style: italic; font-size: 0.75rem; }}
  .hash-change {{ color: #00dc73; font-size: 0.7rem; opacity: 0.7; }}
  .ts {{ color: #6b7280; font-size: 0.7rem; }}
  .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #2a2e3a; font-size: 0.7rem; color: #6b7280; }}
</style>
</head>
<body>
<h1>pruv provenance: {name}</h1>
<span class="status">{status_text}</span>
<div class="meta"><strong>type:</strong> {content_type} &middot; <strong>creator:</strong> {creator} &middot; <strong>modifications:</strong> {transition_count}</div>
<div class="meta"><strong>chain:</strong> {chain_id}</div>
<div class="meta">{verify_message}</div>

<div class="section">
  <div class="section-title">hashes</div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
    <div>
      <div class="hash-label">origin hash</div>
      <div class="hash-block">{origin_hash}</div>
    </div>
    <div>
      <div class="hash-label">current hash</div>
      <div class="hash-block">{current_hash}</div>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-title">modification timeline</div>
  <div id="timeline"></div>
</div>

<div class="footer">exported from pruv &middot; self-verifying provenance receipt</div>
<script>
const timeline = {timeline_json};
const container = document.getElementById('timeline');
if (timeline.length === 0) {{
  container.innerHTML = '<div style="color:#6b7280;font-size:0.8rem;padding:1rem 0;">No modifications — artifact is in its original state.</div>';
}} else {{
  timeline.forEach(t => {{
    const div = document.createElement('div');
    div.className = 'transition';
    const ts = t.timestamp ? new Date(t.timestamp * 1000).toISOString() : '';
    div.innerHTML = `
      <span class="ts">#${{t.index}} &middot; ${{ts}}</span><br>
      <span class="modifier">${{t.modifier}}</span>
      ${{t.reason ? `<span class="reason"> &mdash; ${{t.reason}}</span>` : ''}}<br>
      <span class="hash-change">${{t.previous_hash}}... &rarr; ${{t.new_hash}}...</span>
    `;
    container.appendChild(div);
  }});
}}
</script>
</body>
</html>"""

    return HTMLResponse(content=html_content)
