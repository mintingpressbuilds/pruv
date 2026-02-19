"""Identity routes — agent identity registration, actions, and verification."""

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
    IdentityActRequest,
    IdentityListResponse,
    IdentityRegister,
    IdentityResponse,
    IdentityVerifyResponse,
)
from ..services.identity_service import identity_service

router = APIRouter(prefix="/v1/identity", tags=["identity"])


@router.post("/register", response_model=IdentityResponse)
async def register_identity(
    body: IdentityRegister,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Register a new agent identity.

    Creates an Ed25519 keypair, a pruv chain, and a registration entry.
    Returns the identity with its pi_ address and public key.
    """
    identity = identity_service.register(
        user_id=user["id"],
        name=body.name,
        agent_type=body.agent_type,
        metadata=body.metadata,
    )
    return identity


@router.get("", response_model=IdentityListResponse)
async def list_identities(
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """List all identities for the current user."""
    identities = identity_service.list_identities(user["id"])
    return {"identities": identities, "total": len(identities)}


@router.get("/{identity_id}", response_model=IdentityResponse)
async def get_identity(
    identity_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get an identity by its pi_ address."""
    identity = identity_service.get_identity(identity_id, user["id"])
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity


@router.post("/{identity_id}/act")
async def record_action(
    identity_id: str,
    body: IdentityActRequest,
    user: dict[str, Any] = Depends(require_write),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Record an action for an identity.

    Appends an entry to the identity's chain.
    """
    entry = identity_service.act(
        identity_id=identity_id,
        user_id=user["id"],
        action=body.action,
        data=body.data,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Identity not found")
    return entry


@router.get("/{identity_id}/verify", response_model=IdentityVerifyResponse)
async def verify_identity(
    identity_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Verify an identity's chain integrity."""
    result = identity_service.verify(identity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Identity not found")
    return result


@router.get("/{identity_id}/history")
async def get_history(
    identity_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get action history for an identity, most recent first."""
    history = identity_service.get_history(identity_id, limit=limit, offset=offset)
    if history is None:
        raise HTTPException(status_code=404, detail="Identity not found")
    return {"actions": history, "total": len(history)}


@router.get("/{identity_id}/receipt", response_class=HTMLResponse)
async def get_identity_receipt(
    identity_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Export identity as a self-verifying HTML receipt.

    Shows: agent name, type, address, public key, action timeline,
    verification status.
    """
    identity = identity_service.get_identity(identity_id, user["id"])
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    verification = identity_service.verify(identity_id)
    history = identity_service.get_history(identity_id, limit=100)

    name = html_mod.escape(identity["name"])
    agent_type = html_mod.escape(identity.get("agent_type", "custom"))
    public_key = html_mod.escape(identity["public_key"])
    address = html_mod.escape(identity_id)
    chain_id = html_mod.escape(identity["chain_id"])

    verified = verification and verification.get("valid", False)
    status_text = "VERIFIED" if verified else "BROKEN"
    status_color = "#00dc73" if verified else "#ef4444"
    action_count = verification.get("action_count", 0) if verification else 0
    verify_message = html_mod.escape(
        verification.get("message", "") if verification else ""
    )

    actions_json = json.dumps(
        [
            {
                "index": a.get("index", i),
                "operation": a.get("operation", "unknown"),
                "timestamp": a.get("timestamp", 0),
                "x": a.get("x", ""),
                "y": a.get("y", ""),
                "xy": a.get("xy", ""),
            }
            for i, a in enumerate(history or [])
        ],
        indent=2,
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>pruv identity: {name}</title>
<style>
  body {{ font-family: 'JetBrains Mono', monospace; background: #0f1117; color: #f3f4f6; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.2rem; color: #00dc73; margin-bottom: 0.5rem; }}
  .status {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; background: {status_color}20; color: {status_color}; border: 1px solid {status_color}40; margin-bottom: 1rem; }}
  .meta {{ font-size: 0.75rem; color: #6b7280; margin-bottom: 0.5rem; }}
  .meta strong {{ color: #f3f4f6; }}
  .section {{ margin: 1.5rem 0; }}
  .section-title {{ font-size: 0.85rem; color: #00dc73; margin-bottom: 0.5rem; font-weight: bold; }}
  .key-block {{ background: #1a1d27; border: 1px solid #2a2e3a; border-radius: 0.5rem; padding: 0.75rem; font-size: 0.7rem; word-break: break-all; color: #9ca3af; }}
  .action {{ border-left: 2px solid #2a2e3a; padding: 0.5rem 1rem; margin-bottom: 0.25rem; font-size: 0.8rem; }}
  .action:hover {{ border-color: #00dc73; }}
  .op {{ color: #f3f4f6; font-weight: bold; }}
  .ts {{ color: #6b7280; font-size: 0.7rem; }}
  .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #2a2e3a; font-size: 0.7rem; color: #6b7280; }}
</style>
</head>
<body>
<h1>pruv identity: {name}</h1>
<span class="status">{status_text}</span>
<div class="meta"><strong>address:</strong> {address}</div>
<div class="meta"><strong>type:</strong> {agent_type} &middot; <strong>actions:</strong> {action_count} &middot; <strong>chain:</strong> {chain_id}</div>
<div class="meta">{verify_message}</div>

<div class="section">
  <div class="section-title">public key</div>
  <div class="key-block">{public_key}</div>
</div>

<div class="section">
  <div class="section-title">action history</div>
  <div id="actions"></div>
</div>

<div class="footer">exported from pruv &middot; self-verifying identity receipt</div>
<script>
const actions = {actions_json};
const container = document.getElementById('actions');
actions.forEach(a => {{
  const div = document.createElement('div');
  div.className = 'action';
  const ts = a.timestamp ? new Date(a.timestamp * 1000).toISOString() : '';
  div.innerHTML = `<span class="ts">#${{a.index}} &middot; ${{ts}}</span><br><span class="op">${{a.operation}}</span>`;
  container.appendChild(div);
}});
</script>
</body>
</html>"""

    return HTMLResponse(content=html_content)
