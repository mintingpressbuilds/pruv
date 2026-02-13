# pruv

**Prove what happened.** Cryptographic verification for any system.

Every operation transforms state. pruv captures the before (X), the after (Y), and creates cryptographic proof (XY) that the transformation happened. Chain these together. Verify independently. Prove everything.

```
X → Y → XY

X  = State before (hash)
Y  = State after (hash)
XY = Cryptographic proof of transformation
```

## Packages

| Package | Install | Purpose |
|---------|---------|---------|
| xycore | `pip install xycore` | The XY primitive (standalone, zero deps) |
| pruv | `pip install pruv` | Full SDK with scanner, wrappers, cloud sync |

## Quick Start

```python
from pruv import xy_wrap

wrapped = xy_wrap(my_agent)
result = await wrapped.run("Fix the bug")
print(result.receipt.hash)
```

## The Chain Rule

```
Entry[N].x == Entry[N-1].y

If ANY entry is modified, the chain breaks.
Verification walks the chain and detects tampering instantly.
```

## Platform

| Component | Domain | Purpose |
|-----------|--------|---------|
| xycore | `pip install xycore` | The XY primitive |
| pruv | `pip install pruv` | SDK with scanner, wrappers, cloud sync |
| api.pruv.dev | FastAPI | Cloud storage, verification, export |
| app.pruv.dev | Next.js 16+ | Dashboard, chain explorer, receipts |
| pruv.dev | Next.js 16+ | Marketing, pricing, industries |
| docs.pruv.dev | Mintlify | Documentation |

## Environment Variables

```bash
PRUV_API_KEY=pv_live_…
PRUV_AUTO_REDACT=true
PRUV_AUTO_CHECKPOINT=true
```

## Monorepo Structure

```
pruv/
├── packages/
│   ├── xycore/          # pip install xycore
│   └── pruv/            # pip install pruv
├── apps/
│   ├── api/             # api.pruv.dev (FastAPI)
│   ├── dashboard/       # app.pruv.dev (Next.js 16+)
│   └── web/             # pruv.dev (Next.js 16+)
└── docs/                # docs.pruv.dev (Mintlify)
```

## License

MIT
