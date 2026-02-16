# pruv

[![xycore](https://img.shields.io/badge/xycore-v1.0.1-green)](https://pypi.org/project/xycore/)
[![pruv](https://img.shields.io/badge/pruv-v1.0.1-green)](https://pypi.org/project/pruv/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Prove what happened.**

Cryptographic verification protocol for any system. Two lines of code. Full proof chain.

```
pip install pruv
```

-----

### The problem

Your AI agent just modified 40 files, made 12 API calls, and deployed to production. What actually happened?

Logs say "completed successfully." Cool. Prove it.

-----

### Two lines. Full proof.

```python
from pruv import xy_wrap

wrapped = xy_wrap(my_agent)
result = await wrapped.run("Fix the login bug")
```

That's it. Every action your agent took is now captured with cryptographic proof. Every file read. Every file written. Every command run. Before state hashed. After state hashed. Chained together. Independently verifiable.

```
print(result.receipt)

# Agent Receipt: xy_a7f3c28e91b4
# Task: Fix the login bug
# Actions: 23
# Verified: 23/23
# State: 8f3a1c → d4e6f7
# Status: ✓ all verified
```

-----

### The protocol

Every operation transforms state. pruv captures both sides and creates proof.

```
  X                    Y
(before)             (after)
  │                    │
  └────────┬───────────┘
           │
          XY
    (cryptographic proof)
```

Chain them together. Each entry's X must equal the previous entry's Y. Break one entry, the chain breaks. Verification detects exactly where.

```
Entry 0       Entry 1       Entry 2       Entry 3
┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
│ X: ø │─────▶│ X:Y₀ │─────▶│ X:Y₁ │─────▶│ X:Y₂ │
│ Y:Y₀ │      │ Y:Y₁ │      │ Y:Y₂ │      │ Y:Y₃ │
│XY:h₀ │      │XY:h₁ │      │XY:h₂ │      │XY:h₃ │
└──────┘      └──────┘      └──────┘      └──────┘
```

Tamper with entry 1? Verification catches it instantly:

```python
from pruv import XYChain

chain = XYChain(name="production")
valid, break_index = chain.verify()

# valid: False
# break_index: 1
```

-----

### Scan your project

```python
from pruv import scan

graph = scan("./my-project")
```

pruv reads your codebase and maps everything — services, dependencies, env vars, connections, frameworks. No config files. No manual setup. It reads the code.

```
$ pruv scan

  Services (3)
    ✓ FastAPI backend     python   port 8000
    ✓ Next.js frontend    typescript
    ✓ Stripe webhook      external

  Connections
    frontend → backend    via NEXT_PUBLIC_API_URL
    backend → Supabase    via DATABASE_URL
    backend → Stripe      via STRIPE_SECRET_KEY

  Env Vars
    9 defined · 1 missing · 2 shared

  Graph hash: a7f3c28e91b4
```

Run it again next week. Diff the two scans. See exactly what changed in your architecture — new services, removed connections, changed env vars. Architecture version control from source code.

-----

### Time travel

Open the dashboard. Grab the slider. Drag backward.

The system state reconstructs at any point in the chain. Not a log entry — the actual state as it existed at that moment. Click any entry to see X on the left, Y on the right. Syntax-highlighted diff. The exact change.

Compare any two points. Entry 12 vs entry 187. What changed between those moments? Everything laid out visually.

An agent broke something at 2am? Hit replay. Watch every action animate through the timeline. Find the exact moment it went wrong. See the state before and after. Click restore. One click. Back to the exact checkpoint state, verified by hash.

-----

### Works with anything

```python
# Any AI agent framework
from pruv import xy_wrap

# LangChain
wrapped = xy_wrap(langchain_agent)

# CrewAI
wrapped = xy_wrap(crew)

# OpenAI Agents
wrapped = xy_wrap(openai_agent)

# Any function
@xy_wrap
async def my_workflow(task: str):
    # your code here
    pass

# Any class
wrapped = xy_wrap(my_custom_agent)
```

No framework favorites. No special integrations. One function wraps anything callable.

-----

### Checkpoints

```python
from pruv import CheckpointManager

manager = CheckpointManager(chain, project_dir="./my-project")

# Snapshot current state
checkpoint = manager.create("before-refactor")

# Agent does its thing...

# Something went wrong? Preview what restore will change
preview = manager.preview_restore(checkpoint.id)

# Restore to checkpoint
manager.restore(checkpoint.id)

# Or just quick undo
manager.quick_undo()
```

Full state snapshots with diff preview. See exactly what will change before you restore. One-click undo to the last checkpoint.

-----

### Digital signatures

```python
from xycore import generate_keypair, sign_entry

private_key, public_key = generate_keypair()

# Sign entries — non-repudiation, signer cannot deny
wrapped = xy_wrap(my_agent, sign=True, private_key=private_key)
```

Ed25519 signatures. The signer cannot deny they performed the operation. Verification works independently — anyone with the public key can verify, no pruv account needed.

-----

### Approval gates

```python
wrapped = xy_wrap(
    my_agent,
    approval_webhook="https://my-api.com/approve",
    approval_operations=["file.write", "deploy"]
)
```

High-risk operations pause and wait for human approval via webhook. The agent can read files all day. The moment it tries to write or deploy, a human has to approve. Configurable timeout. Configurable operations.

-----

### Receipts

Every operation produces a receipt — a cryptographic proof-of-work.

```
┌─────────────────────────────────────────┐
│                                         │
│  pruv receipt                           │
│                                         │
│  Task:     Fix the login bug            │
│  Agent:    claude-sonnet-4-20250514              │
│  Duration: 3m 42s                       │
│                                         │
│  Actions:  23                           │
│  Verified: 23/23 ✓                      │
│                                         │
│  X: 8f3a1c2e  (before)                  │
│  Y: d4e6f71a  (after)                   │
│  XY: xy_a7f3c28e91b4...                 │
│                                         │
│  Chain: 47 entries · intact             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  ✓ Verified by pruv             │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

Export as PDF. Embed as badge. Share via link. The recipient can independently verify without a pruv account.

-----

### Cloud optional

```python
# Local only — works forever, zero dependencies
from xycore import XYChain
chain = XYChain(name="local")

# Or sync to cloud for dashboard, sharing, team features
wrapped = xy_wrap(my_agent, api_key="pv_live_...")
```

xycore is zero dependencies. Standard library only. Works offline. Works without an account. Works without the cloud. The protocol needs nothing.

The cloud gives you the dashboard, team collaboration, shareable links, embeddable badges, and PDF export. It's optional.

-----

### Financial verification chains

Payments are state transformations. Balance before. Balance after. pruv proves the math.

```python
from pruv import PaymentChain

ledger = PaymentChain("order-7291", api_key="pv_live_...")

# Deposit funds
ledger.deposit("merchant", 10000.00, source="bank", reference="ACH-4401")

# Record transfers — each one creates a cryptographic balance proof
ledger.transfer("merchant", "customer_123", 189.00, reference="pi_3abc")
ledger.transfer("merchant", "customer_456", 64.50, reference="pi_3def")
```

Every transfer hashes the balances before and after, then links them into the chain. The conservation law is enforced — total in equals total out. No money created. No money destroyed.

```
Before:  merchant=$10,000.00
After:   merchant=$9,746.50  customer_123=$189.00  customer_456=$64.50

X  = hash(balances_before)
Y  = hash(balances_after)
XY = hash(X + "transfer" + Y + timestamp)   # xy_<sha256>
```

Each transfer returns a receipt — cryptographic proof that the balance change happened and the books stayed balanced:

```
┌─────────────────────────────────────────┐
│                                         │
│  pruv payment receipt                   │
│                                         │
│  Chain:    order-7291                   │
│  Type:     transfer                     │
│  Source:   stripe · pi_3abc             │
│                                         │
│  Sender:   merchant                     │
│  Recipient:customer_123                 │
│  Amount:   $189.00                      │
│                                         │
│  Before:   merchant=$10,000.00          │
│  After:    merchant=$9,811.00           │
│            customer_123=$189.00         │
│                                         │
│  X: 3e7a91c4  (balances before)         │
│  Y: b8d2f106  (balances after)          │
│  XY: xy_7c4f8a2e19d3...                │
│                                         │
│  Balanced: ✓  Conservation held         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  ✓ Verified by pruv             │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

Verify the entire ledger in one call:

```python
result = ledger.verify_payments()

# payment_count: 2
# verified_count: 2/2
# all_valid: True
# final_balances: {'merchant': 9746.50, 'customer_123': 189.00, 'customer_456': 64.50}
# total_volume: 253.50
```

Verification recomputes every hash, checks every link, and confirms conservation at each step. Tamper with a single entry — the proof breaks and reports exactly where. Works with the API endpoint (`/v1/chains/{id}/verify-payments`) or fully offline with xycore's `BalanceProof` primitive.

Built for compliance. SOX, PCI-DSS, MiFID II. Pair with digital signatures for non-repudiation. Pair with approval gates for multi-signer workflows on high-value transfers.

-----

### Not logging. Proof.

|Approach|What you get                                  |
|--------|----------------------------------------------|
|Logs    |"Here's what happened, trust us"              |
|Traces  |"Here's the flow, trust our database"         |
|**pruv**|"Here's cryptographic proof — verify yourself"|

-----

### Install

```bash
pip install xycore    # protocol only, zero deps
pip install pruv      # full SDK
```

### Links

- [pruv.dev](https://pruv.dev) — marketing site
- [Dashboard](https://app.pruv.dev) — chain explorer, time travel, receipts
- [Docs](https://docs.pruv.dev) — full documentation
- [API Reference](https://api.pruv.dev/docs) — REST API
- [xycore on PyPI](https://pypi.org/project/xycore/) — zero-dependency protocol
- [pruv on PyPI](https://pypi.org/project/pruv/) — full SDK
- [Follow on X](https://x.com/pruvxy) — @pruvxy

-----

**X → Y → Proof.**
