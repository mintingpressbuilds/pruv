# pruv

[![xycore](https://img.shields.io/badge/xycore-v1.0.1-green)](https://pypi.org/project/xycore/)
[![pruv](https://img.shields.io/badge/pruv-v1.0.1-green)](https://pypi.org/project/pruv/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Prove what happened.**

A deploy pipeline pushed to production at 2am. A payment moved between three accounts. A config change cascaded through 14 services. A workflow touched customer data across two organizations.

Your logs say "completed successfully."

Your auditor asks for proof. Your client asks for proof. Your regulator asks for proof.

Logs aren't proof.

-----

### Logs vs. proof

|Approach|What you get                                     |
|--------|-------------------------------------------------|
|Logs    |"Here's what happened, trust us"                 |
|Traces  |"Here's the flow, trust our database"            |
|**pruv**|"Here's cryptographic proof — verify it yourself"|

pruv captures every operation in a system — every state change, every file touched, every transaction, every handoff — and chains them into a cryptographic proof that anyone can independently verify. No pruv account needed. No trust required.

```
pip install pruv
```

-----

### What proof looks like

This is a pruv receipt. Every operation produces one.

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
│  X: 8f3a1c2e  (state before)            │
│  Y: d4e6f71a  (state after)             │
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

Export as PDF. Embed as badge. Share via link. The recipient verifies independently — no account, no login, no trust required.

It took two lines of code to generate this:

```python
from pruv import xy_wrap

wrapped = xy_wrap(my_service)
result = await wrapped.run("Fix the login bug")
```

-----

### Something broke at 2am

An automated process ran overnight. Production is down. Everyone's asking what happened.

Open the dashboard. Grab the timeline slider. Drag backward.

The system state reconstructs at any point in the chain. Not a log entry — the actual state as it existed at that moment. Click any entry. See state before on the left, state after on the right. Syntax-highlighted diff. The exact change.

Compare any two points. Entry 12 vs entry 187. What changed between those moments? Everything, laid out visually.

Find the exact moment it went wrong. See the state before. Click restore. One click. Back to the verified checkpoint. Done.

```python
from pruv import CheckpointManager

manager = CheckpointManager(chain, project_dir="./my-project")

# Snapshot current state
checkpoint = manager.create("before-refactor")

# System does its thing...

# Something went wrong? Preview what changes before restoring
preview = manager.preview_restore(checkpoint.id)

# Restore to checkpoint
manager.restore(checkpoint.id)

# Or just undo the last action
manager.quick_undo()
```

-----

### Who needs this

Any system where something changes state and someone eventually asks "what happened?" — that's where pruv lives. It's a verification protocol for operations.

**Operations & Infrastructure** — A deploy pipeline pushes to production. A config change cascades through 14 services. A database migration runs at 3am. Something breaks. The postmortem starts with "we think what happened was…" — pruv replaces that with cryptographic proof of exactly what changed, when, and in what order. Rollback to any verified checkpoint.

**Financial Systems** — Money moves between accounts, platforms, and entities. Reconciliation is a manual nightmare. Auditors ask for proof that the books balance. pruv enforces conservation cryptographically — total in equals total out, verified at every step. Built for SOX, PCI-DSS, MiFID II. Not a log that says the math worked. Proof that it did.

**Healthcare & Compliance** — A patient record gets modified. A prescription gets filled. A prior auth gets submitted. Regulators don't want to hear what your system logged — they want to verify independently. pruv gives every state change in a regulated workflow a cryptographic receipt that a third party can audit without access to your systems.

**AI Agents & Automation** — An agent modifies 40 files, makes 12 API calls, and deploys to production. A multi-agent pipeline hands off between three systems. An automated workflow touches customer data. When something goes wrong — or when someone just needs to know what happened — "check the logs" isn't an answer. Every action is captured with before-and-after state hashes, chained and independently verifiable.

**Supply Chain & Logistics** — Goods move through suppliers, warehouses, customs, carriers, and retailers. Each handoff is a state change. Each participant has their own system. pruv gives every handoff a cryptographic proof that both parties can verify. Disputes become trivial — the chain shows exactly where state diverged.

**Legal & Contracts** — A contract moves through drafts, reviews, approvals, and signatures. Who changed what, and when? Version history in Google Docs isn't evidence. A pruv chain over a document's lifecycle is a tamper-evident record of every modification, every approval gate, every signature — exportable as proof in a dispute.

**Multi-Party Workflows** — Any process where work crosses organizational boundaries. Agency does work, client reviews, vendor fulfills, auditor inspects. Each handoff is a trust gap. pruv closes it — every party can independently verify what the other parties did without trusting their systems.

If state changes and accountability matters, you need proof, not logs.

-----

### Financial verification

Payments are state transformations. Balance before. Balance after. pruv proves the math.

```python
from pruv import PaymentChain

ledger = PaymentChain("order-7291", api_key="pv_live_...")

# Deposit funds
ledger.deposit("merchant", 10000.00, source="bank", reference="ACH-4401")

# Each transfer creates a cryptographic balance proof
ledger.transfer("merchant", "customer_123", 189.00, reference="pi_3abc")
ledger.transfer("merchant", "customer_456", 64.50, reference="pi_3def")
```

Every transfer hashes the balances before and after, then links them into the chain. The conservation law is enforced cryptographically — total in must equal total out. No money created. No money destroyed.

```
Before:  merchant=$10,000.00
After:   merchant=$9,746.50  customer_123=$189.00  customer_456=$64.50

X  = hash(balances_before)
Y  = hash(balances_after)
XY = hash(X + "transfer" + Y + timestamp)
```

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

Tamper with a single entry — the chain breaks and reports exactly where. Works via the API (`/v1/chains/{id}/verify-payments`) or fully offline with xycore's `BalanceProof` primitive.

Built for compliance. SOX, PCI-DSS, MiFID II. Pair with digital signatures for non-repudiation. Pair with approval gates for multi-signer workflows on high-value transfers.

-----

### Works with anything

```python
from pruv import xy_wrap

# Any function
@xy_wrap
async def my_workflow(task: str):
    # your code here
    pass

# Any class
wrapped = xy_wrap(my_service)

# Any agent framework
wrapped = xy_wrap(langchain_agent)     # LangChain
wrapped = xy_wrap(crew)                # CrewAI
wrapped = xy_wrap(openai_agent)        # OpenAI Agents
```

No framework favorites. No special integrations. One function wraps anything callable — services, scripts, pipelines, agents, workflows.

-----

### Approval gates

High-risk operations pause and wait for a human.

```python
wrapped = xy_wrap(
    my_service,
    approval_webhook="https://my-api.com/approve",
    approval_operations=["file.write", "deploy"]
)
```

The system can read all day. The moment it tries to write or deploy, a human has to approve. Every approval is recorded in the chain — who approved, when, what they approved. Cryptographically signed. Non-repudiable.

-----

### Digital signatures

```python
from xycore import generate_keypair

private_key, public_key = generate_keypair()

wrapped = xy_wrap(my_service, sign=True, private_key=private_key)
```

Ed25519 signatures on every entry. The signer cannot deny they performed the operation. Anyone with the public key can verify independently.

-----

### Scan your project

Map your entire codebase — services, dependencies, env vars, connections — from source code. No config files. No manual setup.

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

Run it again next week. Diff the two scans. See exactly what changed in your architecture. Architecture version control, derived from source code.

-----

### How the protocol works

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

Chain them together. Each entry's X must match the previous entry's Y. Break one link, the whole chain breaks. Verification detects exactly where.

```
Entry 0       Entry 1       Entry 2       Entry 3
┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
│ X: ø │─────▶│ X:Y₀ │─────▶│ X:Y₁ │─────▶│ X:Y₂ │
│ Y:Y₀ │      │ Y:Y₁ │      │ Y:Y₂ │      │ Y:Y₃ │
│XY:h₀ │      │XY:h₁ │      │XY:h₂ │      │XY:h₃ │
└──────┘      └──────┘      └──────┘      └──────┘
```

```python
from pruv import XYChain

chain = XYChain(name="production")
valid, break_index = chain.verify()
```

-----

### Cloud optional

```python
# Local only — works forever, zero dependencies
from xycore import XYChain
chain = XYChain(name="local")

# Or sync to cloud for dashboard, sharing, team features
wrapped = xy_wrap(my_service, api_key="pv_live_...")
```

xycore is the protocol. Zero dependencies. Standard library only. Works offline. Works without an account. Works forever.

The cloud adds the dashboard, team collaboration, shareable receipt links, embeddable badges, and PDF export. It's optional.

-----

### Install

```bash
pip install xycore    # protocol only, zero deps
pip install pruv      # full SDK
```

### Links

- [pruv.dev](https://pruv.dev) — product site
- [Dashboard](https://app.pruv.dev) — chain explorer, time travel, receipts
- [Docs](https://docs.pruv.dev) — full documentation
- [API Reference](https://api.pruv.dev/docs) — REST API
- [xycore on PyPI](https://pypi.org/project/xycore/) — zero-dependency protocol
- [pruv on PyPI](https://pypi.org/project/pruv/) — full SDK
- [Follow on X](https://x.com/pruvxy) — @pruvxy

-----

**X → Y → Proof.**
