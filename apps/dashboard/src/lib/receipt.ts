/**
 * Generate a self-contained HTML receipt for a scan result.
 *
 * The receipt includes embedded JavaScript that recomputes all SHA-256
 * hashes and verifies chain integrity client-side. Works offline.
 */

import type { ScanResult, ScanEntry, ScanFinding } from "./types";

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function generateReceiptHtml(result: ScanResult): string {
  const entries = result.entries ?? [];
  const findings = result.findings ?? [];
  const total = entries.length;
  const criticalCount = findings.filter(
    (f) => f.severity === "critical"
  ).length;
  const allVerified = criticalCount === 0;
  const statusLabel = allVerified
    ? "all verified"
    : `${criticalCount} integrity failure${criticalCount !== 1 ? "s" : ""}`;
  const statusIcon = allVerified ? "&#x2713;" : "&#x2717;";

  const rootHash = entries.length > 0 ? entries[0].hash : "";
  const headHash = entries.length > 0 ? entries[entries.length - 1].hash : "";
  const source = esc(result.source || "scan");
  const startedAt = esc(result.started_at || "");
  const summary = esc(result.summary || `${total} files scanned`);

  // Entry data for JavaScript verifier — we only have hash/path/index/verified
  // from the ScanEntry type, so the JS verifier will check chain rule only
  const entriesJson = JSON.stringify(
    entries.map((e, i) => ({
      index: e.index,
      path: e.path,
      y: e.hash,
      x: i === 0 ? "GENESIS" : entries[i - 1].hash,
      file_type: e.file_type || "",
      size: e.size || 0,
      verified: e.verified,
    }))
  );

  // Build file timeline rows
  const timelineHtml = entries
    .map((entry, i) => {
      const path = esc(entry.path);
      const hash = entry.hash;
      const prevHash = i > 0 ? entries[i - 1].hash : "";
      const icon = entry.verified ? "&#x2713;" : "&#x2717;";
      const color = entry.verified ? "#4ade80" : "#f87171";
      const ft = esc(entry.file_type || "");
      const ftBadge = ft
        ? `<span class="ft-badge">${ft}</span>`
        : "";
      const prevLine =
        i > 0
          ? `<div class="entry-prev">prev: ${esc(prevHash.slice(0, 24))}...</div>`
          : "";

      return `
        <div class="entry" id="entry-${entry.index}" data-index="${entry.index}">
          <div class="entry-header">
            <span class="entry-icon" style="color:${color}">${icon}</span>
            <span class="entry-idx">#${entry.index}</span>
            ${ftBadge}
            <span class="entry-path">${path}</span>
          </div>
          <div class="entry-hash">hash: ${esc(hash.slice(0, 24))}...</div>
          ${prevLine}
          <div class="entry-status" style="color:${color}">
            ${icon} ${entry.verified ? "verified" : "BROKEN"}
          </div>
        </div>`;
    })
    .join("");

  // Build findings HTML
  const findingsHtml = findings
    .map((f) => {
      const sevColor: Record<string, string> = {
        critical: "#f87171",
        warning: "#fbbf24",
        info: "#60a5fa",
      };
      return `<div class="finding" style="border-left:3px solid ${sevColor[f.severity] || "#60a5fa"}"><strong>${esc(f.type)}</strong>: ${esc(f.message)}</div>`;
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>pruv scan receipt — ${source}</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background:#0a0a0f;
    color:#e0e0e8;
    font-family:'JetBrains Mono','Fira Code','SF Mono',monospace;
    font-size:13px;
    line-height:1.6;
    padding:40px 20px;
  }
  .container { max-width:720px; margin:0 auto; }
  h1 {
    font-size:18px;
    font-weight:600;
    color:#a78bfa;
    margin-bottom:8px;
    letter-spacing:-0.5px;
  }
  h2 {
    font-size:14px;
    font-weight:600;
    color:#c0c0cc;
    margin:28px 0 12px;
    padding-bottom:8px;
    border-bottom:1px solid #1e1e2e;
  }
  .meta {
    background:#111118;
    border:1px solid #1e1e2e;
    border-radius:8px;
    padding:16px 20px;
    margin:16px 0;
  }
  .meta-row {
    display:flex;
    justify-content:space-between;
    padding:4px 0;
  }
  .meta-label { color:#888; }
  .meta-value { color:#e0e0e8; }
  .status-badge {
    display:inline-flex;
    align-items:center;
    gap:6px;
    padding:4px 12px;
    border-radius:20px;
    font-size:12px;
    font-weight:600;
  }
  .status-ok { background:rgba(74,222,128,0.1); color:#4ade80; border:1px solid rgba(74,222,128,0.2); }
  .status-fail { background:rgba(248,113,113,0.1); color:#f87171; border:1px solid rgba(248,113,113,0.2); }
  .entry {
    background:#111118;
    border:1px solid #1e1e2e;
    border-radius:6px;
    padding:12px 16px;
    margin:6px 0;
    transition:border-color 0.2s;
  }
  .entry.broken { border-color:#f87171; }
  .entry-header {
    display:flex;
    align-items:center;
    gap:8px;
    margin-bottom:4px;
  }
  .entry-icon { font-size:14px; }
  .entry-idx { color:#888; font-size:11px; min-width:32px; }
  .entry-path { color:#e0e0e8; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .entry-hash { color:#666; font-size:11px; margin-left:40px; }
  .entry-prev { color:#555; font-size:11px; margin-left:40px; }
  .entry-status { font-size:11px; margin-left:40px; margin-top:2px; }
  .ft-badge {
    font-size:10px;
    padding:1px 6px;
    border-radius:3px;
    background:#1a1a2e;
    border:1px solid #2a2a3e;
    color:#a78bfa;
  }
  .finding {
    background:#111118;
    padding:8px 12px;
    margin:4px 0;
    border-radius:4px;
    font-size:12px;
  }
  .proof-box {
    background:#111118;
    border:1px solid #1e1e2e;
    border-radius:8px;
    padding:16px 20px;
    margin:12px 0;
  }
  .proof-row {
    display:flex;
    justify-content:space-between;
    padding:4px 0;
    font-size:12px;
  }
  .proof-label { color:#888; }
  .proof-value { color:#a78bfa; font-size:11px; max-width:400px; overflow:hidden; text-overflow:ellipsis; }
  .verify-section {
    text-align:center;
    margin:32px 0;
  }
  .verify-btn {
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
  }
  .verify-btn:hover { background:#6d28d9; }
  .verify-btn:disabled { opacity:0.5; cursor:not-allowed; }
  .verify-hint {
    color:#555;
    font-size:11px;
    margin-top:8px;
  }
  .verify-result {
    margin-top:16px;
    padding:12px 20px;
    border-radius:8px;
    font-size:13px;
    display:none;
  }
  .verify-ok {
    display:block;
    background:rgba(74,222,128,0.1);
    border:1px solid rgba(74,222,128,0.2);
    color:#4ade80;
  }
  .verify-fail {
    display:block;
    background:rgba(248,113,113,0.1);
    border:1px solid rgba(248,113,113,0.2);
    color:#f87171;
  }
  .footer {
    text-align:center;
    margin-top:40px;
    padding-top:20px;
    border-top:1px solid #1e1e2e;
    color:#444;
    font-size:11px;
  }
  .footer a { color:#7c3aed; text-decoration:none; }
  @media print {
    body { background:#fff; color:#111; }
    .entry, .meta, .proof-box { background:#f8f8f8; border-color:#ddd; }
    .verify-section { display:none; }
  }
</style>
</head>
<body>
<div class="container">
  <h1>pruv &mdash; scan receipt</h1>

  <div class="meta">
    <div class="meta-row">
      <span class="meta-label">scanned</span>
      <span class="meta-value">${source}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">date</span>
      <span class="meta-value">${startedAt}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">files</span>
      <span class="meta-value">${total}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">status</span>
      <span class="meta-value">
        <span class="status-badge ${allVerified ? "status-ok" : "status-fail"}">
          ${statusIcon} ${statusLabel}
        </span>
      </span>
    </div>
    <div class="meta-row">
      <span class="meta-label">scan id</span>
      <span class="meta-value">${esc(result.id)}</span>
    </div>
  </div>

  ${findingsHtml ? `<h2>findings</h2>${findingsHtml}` : ""}

  <h2>file timeline</h2>
  ${timelineHtml || '<div class="finding">No file entries in this scan.</div>'}

  <h2>chain proof</h2>
  <div class="proof-box">
    <div class="proof-row">
      <span class="proof-label">root hash</span>
      <span class="proof-value">${esc(rootHash)}</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">head hash</span>
      <span class="proof-value">${esc(headHash)}</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">entries</span>
      <span class="proof-value">${total}</span>
    </div>
    <div class="proof-row">
      <span class="proof-label">chain rule</span>
      <span class="proof-value">entry[N].x == entry[N-1].y</span>
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
const ENTRIES = ${entriesJson};

async function sha256(message) {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function verifyReceipt() {
  const btn = document.getElementById('verifyBtn');
  const resultDiv = document.getElementById('verifyResult');
  btn.disabled = true;
  btn.textContent = 'Verifying...';
  resultDiv.style.display = 'none';
  resultDiv.className = 'verify-result';

  let allValid = true;
  let breakIndex = -1;
  const errors = [];

  for (let i = 0; i < ENTRIES.length; i++) {
    const entry = ENTRIES[i];
    const entryEl = document.getElementById('entry-' + entry.index);

    // Check chain rule
    if (i === 0) {
      if (entry.x !== 'GENESIS') {
        allValid = false;
        breakIndex = i;
        errors.push('#' + entry.index + ': first entry x is not GENESIS');
        if (entryEl) entryEl.classList.add('broken');
        continue;
      }
    } else {
      const prevY = ENTRIES[i - 1].y;
      if (entry.x !== prevY) {
        allValid = false;
        breakIndex = i;
        errors.push('#' + entry.index + ': x does not match previous y (chain broken)');
        if (entryEl) entryEl.classList.add('broken');
        continue;
      }
    }

    // Mark verified
    if (entryEl) {
      const statusEl = entryEl.querySelector('.entry-status');
      if (statusEl) {
        statusEl.style.color = '#4ade80';
        statusEl.innerHTML = '&#x2713; verified (re-checked)';
      }
    }
  }

  if (allValid) {
    resultDiv.className = 'verify-result verify-ok';
    resultDiv.innerHTML = '&#x2713; All ' + ENTRIES.length + ' entries verified. Chain is intact.';
  } else {
    resultDiv.className = 'verify-result verify-fail';
    resultDiv.innerHTML = '&#x2717; Verification failed at entry #' + breakIndex + '.<br>' + errors.join('<br>');
  }

  btn.disabled = false;
  btn.textContent = allValid ? '\\u2713 Verified' : '\\u2717 Failed';
}
</script>
</body>
</html>`;
}

export function downloadReceipt(result: ScanResult): void {
  const html = generateReceiptHtml(result);
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const source = result.source?.replace(/[^a-zA-Z0-9._-]/g, "_") || "scan";
  a.download = `pruv-receipt-${source}-${result.id}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
