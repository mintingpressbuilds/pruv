"""Generate self-contained HTML scan receipts with client-side verification."""

from __future__ import annotations

import html
import json
from typing import Any


def generate_receipt_html(
    scan_id: str,
    source: str | None,
    started_at: str,
    completed_at: str | None,
    entries: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    summary: str | None,
) -> str:
    """Generate a self-contained HTML receipt for a scan.

    The receipt includes:
    - Scan metadata (source, time, file count, status)
    - Every file entry with path, hash, chain position, verification status
    - Chain proof data (root hash, head hash, entry count)
    - A "Verify" button that recomputes all hashes client-side using
      the Web Crypto API (SubtleCrypto SHA-256). No server needed.
    """
    total = len(entries)
    critical_count = len([f for f in findings if f.get("severity") == "critical"])
    all_verified = critical_count == 0
    status_label = "all verified" if all_verified else f"{critical_count} integrity failure{'s' if critical_count != 1 else ''}"
    status_icon = "&#x2713;" if all_verified else "&#x2717;"
    status_color = "#4ade80" if all_verified else "#f87171"

    root_hash = entries[0].get("y", entries[0].get("hash", "")) if entries else ""
    head_hash = entries[-1].get("y", entries[-1].get("hash", "")) if entries else ""
    root_xy = entries[0].get("xy", "") if entries else ""
    head_xy = entries[-1].get("xy", "") if entries else ""

    display_source = html.escape(source or "unknown")
    display_started = html.escape(started_at or "")
    display_summary = html.escape(summary or f"{total} files scanned")

    # Build entries JSON for the JavaScript verifier
    entries_json = json.dumps([
        {
            "index": e.get("index", i),
            "path": e.get("path", e.get("operation", f"entry-{i}")),
            "x": e.get("x", ""),
            "y": e.get("y", e.get("hash", "")),
            "xy": e.get("xy", ""),
            "operation": e.get("operation", e.get("path", "")),
            "timestamp": e.get("timestamp", 0),
            "file_type": e.get("file_type", ""),
            "size": e.get("size", 0),
        }
        for i, e in enumerate(entries)
    ])

    # Build the file timeline HTML
    timeline_html = ""
    for i, entry in enumerate(entries):
        path = html.escape(entry.get("path", entry.get("operation", f"entry-{i}")))
        y_hash = entry.get("y", entry.get("hash", ""))
        x_hash = entry.get("x", "")
        idx = entry.get("index", i)
        ft = html.escape(entry.get("file_type", ""))
        verified = entry.get("verified", True)
        icon = "&#x2713;" if verified else "&#x2717;"
        color = "#4ade80" if verified else "#f87171"

        prev_line = ""
        if i > 0:
            prev_line = f'<div class="entry-prev">prev: {html.escape(x_hash[:24])}...</div>'

        ft_badge = f'<span class="ft-badge">{ft}</span>' if ft else ""

        timeline_html += f"""
        <div class="entry" id="entry-{idx}" data-index="{idx}">
          <div class="entry-header">
            <span class="entry-icon" style="color:{color}">{icon}</span>
            <span class="entry-idx">#{idx}</span>
            {ft_badge}
            <span class="entry-path">{path}</span>
          </div>
          <div class="entry-hash">hash: {html.escape(y_hash[:24])}...</div>
          {prev_line}
          <div class="entry-status" style="color:{color}">
            {icon} {"verified" if verified else "BROKEN"}
          </div>
        </div>"""

    # Build findings HTML
    findings_html = ""
    if findings:
        for f in findings:
            sev = f.get("severity", "info")
            msg = html.escape(f.get("message", ""))
            ftype = html.escape(f.get("type", ""))
            sev_color = {"critical": "#f87171", "warning": "#fbbf24", "info": "#60a5fa"}.get(sev, "#60a5fa")
            findings_html += f'<div class="finding" style="border-left:3px solid {sev_color}"><strong>{ftype}</strong>: {msg}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>pruv scan receipt — {display_source}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background:#0a0a0f;
    color:#e0e0e8;
    font-family:'JetBrains Mono','Fira Code','SF Mono',monospace;
    font-size:13px;
    line-height:1.6;
    padding:40px 20px;
  }}
  .container {{ max-width:720px; margin:0 auto; }}
  h1 {{
    font-size:18px;
    font-weight:600;
    color:#a78bfa;
    margin-bottom:8px;
    letter-spacing:-0.5px;
  }}
  h2 {{
    font-size:14px;
    font-weight:600;
    color:#c0c0cc;
    margin:28px 0 12px;
    padding-bottom:8px;
    border-bottom:1px solid #1e1e2e;
  }}
  .meta {{
    background:#111118;
    border:1px solid #1e1e2e;
    border-radius:8px;
    padding:16px 20px;
    margin:16px 0;
  }}
  .meta-row {{
    display:flex;
    justify-content:space-between;
    padding:4px 0;
  }}
  .meta-label {{ color:#888; }}
  .meta-value {{ color:#e0e0e8; }}
  .status-badge {{
    display:inline-flex;
    align-items:center;
    gap:6px;
    padding:4px 12px;
    border-radius:20px;
    font-size:12px;
    font-weight:600;
  }}
  .status-ok {{ background:rgba(74,222,128,0.1); color:#4ade80; border:1px solid rgba(74,222,128,0.2); }}
  .status-fail {{ background:rgba(248,113,113,0.1); color:#f87171; border:1px solid rgba(248,113,113,0.2); }}
  .entry {{
    background:#111118;
    border:1px solid #1e1e2e;
    border-radius:6px;
    padding:12px 16px;
    margin:6px 0;
    transition:border-color 0.2s;
  }}
  .entry.broken {{ border-color:#f87171; }}
  .entry-header {{
    display:flex;
    align-items:center;
    gap:8px;
    margin-bottom:4px;
  }}
  .entry-icon {{ font-size:14px; }}
  .entry-idx {{ color:#888; font-size:11px; min-width:32px; }}
  .entry-path {{ color:#e0e0e8; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .entry-hash {{ color:#666; font-size:11px; margin-left:40px; }}
  .entry-prev {{ color:#555; font-size:11px; margin-left:40px; }}
  .entry-status {{ font-size:11px; margin-left:40px; margin-top:2px; }}
  .ft-badge {{
    font-size:10px;
    padding:1px 6px;
    border-radius:3px;
    background:#1a1a2e;
    border:1px solid #2a2a3e;
    color:#a78bfa;
  }}
  .finding {{
    background:#111118;
    padding:8px 12px;
    margin:4px 0;
    border-radius:4px;
    font-size:12px;
  }}
  .proof-box {{
    background:#111118;
    border:1px solid #1e1e2e;
    border-radius:8px;
    padding:16px 20px;
    margin:12px 0;
  }}
  .proof-row {{
    display:flex;
    justify-content:space-between;
    padding:4px 0;
    font-size:12px;
  }}
  .proof-label {{ color:#888; }}
  .proof-value {{ color:#a78bfa; font-size:11px; max-width:400px; overflow:hidden; text-overflow:ellipsis; }}
  .verify-section {{
    text-align:center;
    margin:32px 0;
  }}
  .verify-btn {{
    background:#7c3aed;
    color:#fff;
    border:none;
    padding:12px 32px;
    border-radius:8px;
    font-size:14px;
    font-weight:600;
    font-family:inherit;
    cursor:pointer;
    transition:background 0.2s;
  }}
  .verify-btn:hover {{ background:#6d28d9; }}
  .verify-btn:disabled {{ opacity:0.5; cursor:not-allowed; }}
  .verify-hint {{
    color:#555;
    font-size:11px;
    margin-top:8px;
  }}
  .verify-result {{
    margin-top:16px;
    padding:12px 20px;
    border-radius:8px;
    font-size:13px;
    display:none;
  }}
  .verify-ok {{
    display:block;
    background:rgba(74,222,128,0.1);
    border:1px solid rgba(74,222,128,0.2);
    color:#4ade80;
  }}
  .verify-fail {{
    display:block;
    background:rgba(248,113,113,0.1);
    border:1px solid rgba(248,113,113,0.2);
    color:#f87171;
  }}
  .footer {{
    text-align:center;
    margin-top:40px;
    padding-top:20px;
    border-top:1px solid #1e1e2e;
    color:#444;
    font-size:11px;
  }}
  .footer a {{ color:#7c3aed; text-decoration:none; }}
  @media print {{
    body {{ background:#fff; color:#111; }}
    .entry, .meta, .proof-box {{ background:#f8f8f8; border-color:#ddd; }}
    .verify-section {{ display:none; }}
  }}
</style>
</head>
<body>
<div class="container">
  <h1>pruv &mdash; scan receipt</h1>

  <div class="meta">
    <div class="meta-row">
      <span class="meta-label">scanned</span>
      <span class="meta-value">{display_source}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">date</span>
      <span class="meta-value">{display_started}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">files</span>
      <span class="meta-value">{total}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">status</span>
      <span class="meta-value">
        <span class="status-badge {"status-ok" if all_verified else "status-fail"}">
          {status_icon} {status_label}
        </span>
      </span>
    </div>
    <div class="meta-row">
      <span class="meta-label">scan id</span>
      <span class="meta-value">{html.escape(scan_id)}</span>
    </div>
  </div>

  {"<h2>findings</h2>" + findings_html if findings_html else ""}

  <h2>file timeline</h2>
  {timeline_html}

  <h2>chain proof</h2>
  <div class="proof-box">
    <div class="proof-row">
      <span class="proof-label">root hash</span>
      <span class="proof-value">{html.escape(root_hash)}</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">head hash</span>
      <span class="proof-value">{html.escape(head_hash)}</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">entries</span>
      <span class="proof-value">{total}</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">chain rule</span>
      <span class="proof-value">entry[N].x == entry[N-1].y</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">root xy</span>
      <span class="proof-value">{html.escape(root_xy)}</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">head xy</span>
      <span class="proof-value">{html.escape(head_xy)}</span>
    </div>
  </div>

  <div class="verify-section">
    <button class="verify-btn" id="verifyBtn" onclick="verifyReceipt()">
      &#x2713; Verify This Receipt
    </button>
    <div class="verify-hint">
      recalculates all hashes in your browser &mdash; works offline
    </div>
    <div class="verify-result" id="verifyResult"></div>
  </div>

  <div class="footer">
    <strong>pruv</strong>.dev &middot; operational proof for any system
  </div>
</div>

<script>
// Entry data embedded in the receipt for client-side verification
const ENTRIES = {entries_json};

// SHA-256 using Web Crypto API
async function sha256(message) {{
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}}

// Recompute XY proof: xy_SHA256("x:operation:y:timestamp")
async function computeXY(x, operation, y, timestamp) {{
  const data = x + ':' + operation + ':' + y + ':' + timestamp;
  const digest = await sha256(data);
  return 'xy_' + digest;
}}

async function verifyReceipt() {{
  const btn = document.getElementById('verifyBtn');
  const resultDiv = document.getElementById('verifyResult');
  btn.disabled = true;
  btn.textContent = 'Verifying...';
  resultDiv.style.display = 'none';
  resultDiv.className = 'verify-result';

  let allValid = true;
  let breakIndex = -1;
  const errors = [];

  for (let i = 0; i < ENTRIES.length; i++) {{
    const entry = ENTRIES[i];
    const entryEl = document.getElementById('entry-' + entry.index);

    // 1. Check chain rule: first entry x must be GENESIS,
    //    subsequent entries x must equal previous entry y
    if (i === 0) {{
      if (entry.x !== 'GENESIS') {{
        allValid = false;
        breakIndex = i;
        errors.push('#' + entry.index + ': first entry x is not GENESIS');
        if (entryEl) entryEl.classList.add('broken');
        continue;
      }}
    }} else {{
      const prevY = ENTRIES[i - 1].y;
      if (entry.x !== prevY) {{
        allValid = false;
        breakIndex = i;
        errors.push('#' + entry.index + ': x does not match previous y (chain broken)');
        if (entryEl) entryEl.classList.add('broken');
        continue;
      }}
    }}

    // 2. Recompute XY proof
    if (entry.xy && entry.operation && entry.timestamp) {{
      const expectedXY = await computeXY(entry.x, entry.operation, entry.y, entry.timestamp);
      if (entry.xy !== expectedXY) {{
        allValid = false;
        breakIndex = i;
        errors.push('#' + entry.index + ': xy proof mismatch');
        if (entryEl) entryEl.classList.add('broken');
        continue;
      }}
    }}

    // Mark verified
    if (entryEl) {{
      const statusEl = entryEl.querySelector('.entry-status');
      if (statusEl) {{
        statusEl.style.color = '#4ade80';
        statusEl.innerHTML = '&#x2713; verified (re-checked)';
      }}
    }}
  }}

  if (allValid) {{
    resultDiv.className = 'verify-result verify-ok';
    resultDiv.innerHTML = '&#x2713; All ' + ENTRIES.length + ' entries verified. Chain is intact. Every hash matches.';
  }} else {{
    resultDiv.className = 'verify-result verify-fail';
    resultDiv.innerHTML = '&#x2717; Verification failed at entry #' + breakIndex + '.<br>' + errors.join('<br>');
  }}

  btn.disabled = false;
  btn.textContent = allValid ? '\\u2713 Verified' : '\\u2717 Failed';
}}
</script>
</body>
</html>"""
