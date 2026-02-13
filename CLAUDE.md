# pruv

## What this is

pruv is a cryptographic verification primitive. The core idea: every operation transforms state. Capture the before (X), the after (Y), and create cryptographic proof (XY) that the transformation happened. Chain these together. The chain rule: Entry[N].x must equal Entry[N-1].y. Break one entry, the chain breaks. That's the entire product.

pruv is not a SaaS tool, not an observability platform, not a logging system. It is a primitive — like Stripe's charge object is a primitive for payments, pruv's XY chain is a primitive for verification.

## Architecture

```
pruv-platform/
├── packages/
│   ├── xycore/          # pip install xycore — zero-dependency primitive
│   └── pruv/            # pip install pruv — full SDK
├── apps/
│   ├── api/             # api.pruv.dev — FastAPI backend
│   ├── web/             # pruv.dev — Next.js 16+ marketing site
│   └── dashboard/       # app.pruv.dev — Next.js 16+ dashboard
└── docs/                # docs.pruv.dev — Mintlify
```

### Layer hierarchy

Each layer stands alone. Each layer builds on the one below it without requiring the one above it.

1. **xycore** — The primitive. XYEntry, XYChain, XYReceipt. Hash functions. Chain verification. Digital signatures. Auto-redaction. Zero dependencies. Works offline forever.
1. **pruv SDK** — Scanner, xy_wrap() universal wrapper, checkpoints, approval gates, cloud sync. Depends on xycore.
1. **API** — Cloud storage, verification, export, receipts, shared links. Depends on pruv SDK.
1. **Dashboard** — Chain explorer, time travel, replay, receipt viewer. Depends on API.
1. **Marketing site** — Product pages, industry pages, pricing. Independent.

## Core rules

- Always lowercase "pruv". Never "Pruv" or "PRUV".
- API key prefix: `pv_live_` (production), `pv_test_` (testing)
- XY proof hash format: `xy_{sha256_hex}`
- Chain rule: `Entry[N].x == Entry[N-1].y` — this is inviolable
- First entry's x is `"GENESIS"`
- Auto-redact secrets in all output — Stripe keys, AWS keys, GitHub tokens, passwords, API keys, pruv keys
- Ed25519 for digital signatures
- AES-256-GCM for encryption at rest
- SHA-256 for all hashing
- Next.js 16+ for all frontend
- xycore has ZERO external dependencies

## The primitive

```python
X  = hash_state(state_before)        # SHA-256
Y  = hash_state(state_after)         # SHA-256
XY = compute_xy(x, operation, y, ts) # "xy_{sha256}"

# Chain linking
entry_0.x = "GENESIS"
entry_1.x = entry_0.y
entry_2.x = entry_1.y
# ...
entry_n.x = entry_n-1.y
```

Verification walks the chain. Recomputes every hash. Checks every link. If anything was modified, it reports exactly where the break occurred.

## Key components

### xycore

- `XYEntry` — Single state transformation with optional signature
- `XYChain` — Ordered list of entries with chain rule enforcement
- `XYReceipt` — Summary proof of a complete operation
- `hash_state()` — Deterministic JSON hashing
- `compute_xy()` — Proof hash from x + operation + y + timestamp
- `verify_chain()` — Walk chain, check every link, report break index
- `sign_entry()` / `verify_signature()` — Ed25519 non-repudiation
- `redact_state()` — Remove secrets before storage/display

### pruv SDK

- `scan()` — Scan a project directory, produce a Graph with deterministic hash
- `xy_wrap()` — Universal wrapper for any agent/function/workflow. Captures before state, observes actions, captures after state, produces receipt with cryptographic proof
- `CheckpointManager` — Create snapshots, preview diffs, restore, quick undo
- `ApprovalGate` — Webhook-based human approval for high-risk operations
- `CloudClient` — Sync chains to api.pruv.dev with offline queue

### API (api.pruv.dev)

- `/v1/chains` — CRUD + verify + share
- `/v1/chains/:id/entries` — Append + batch + list
- `/v1/chains/:id/checkpoints` — Create + preview + restore
- `/v1/receipts/:id` — Get + PDF export + embeddable badge
- Auth: API keys (pv_live_ prefix, SHA-256 hashed), OAuth (GitHub, Google)
- Rate limits: Free 60/min, Pro 300/min, Team 1000/min

### Dashboard (app.pruv.dev)

- Chain timeline as vertical line with inline expansion
- Entry detail with X → Y diff view
- Time travel slider
- Quick undo with diff preview
- Replay animation
- Verification animation with break visualization
- Receipt viewer with PDF export

## Environment variables

```
PRUV_API_KEY=pv_live_...
PRUV_AUTO_REDACT=true
PRUV_AUTO_CHECKPOINT=true
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
STRIPE_SECRET_KEY=sk_live_...
NEXTAUTH_SECRET=...
NEXTAUTH_URL=https://app.pruv.dev
```

## Auto-redaction patterns

These patterns are always redacted in chain output, logs, and API responses:

- `sk_live_*`, `sk_test_*` (Stripe)
- `pv_live_*`, `pv_test_*` (pruv)
- `ghp_*`, `gho_*` (GitHub)
- `AKIA*` (AWS)
- `password=*`, `api_key=*`, `secret=*`, `token=*`

## Quality standard

1.0 or it doesn't ship. Every test passes. Every chain verifies. Every API route is authenticated and rate-limited. Every secret is redacted. No exceptions.

## Reference

Full specification: PRUV_BLUEPRINT.md
