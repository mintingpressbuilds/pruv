# pruv

[![xycore](https://img.shields.io/badge/xycore-v1.0.1-green)](https://pypi.org/project/xycore/)
[![pruv](https://img.shields.io/badge/pruv-v1.0.1-green)](https://pypi.org/project/pruv/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**The digital verification layer.**

-----

The digital world has no verification layer.

Every system — every pipeline, every payment, every agent, every workflow — runs on trust. Trust in logs. Trust in databases. Trust in whoever ran the process. That trust is manufactured. There is no way to prove a digital operation happened — in a specific sequence, without tampering — that anyone can verify independently, without trusting the system that produced the record.

pruv is that layer.

```
pip install pruv
```

-----

### The protocol

Every operation transforms state. Something exists before. Something exists after. pruv captures both and creates proof.

```
  X                    Y
(before)             (after)
  │                    │
  └────────┬───────────┘
           │
          XY
    (cryptographic proof)
```

Chain them together. Each entry's X must match the previous entry's Y. Break one link — the chain breaks. Verification detects exactly where.

```
Entry 0       Entry 1       Entry 2       Entry 3
┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
│ X: ø │─────▶│ X:Y₀ │─────▶│ X:Y₁ │─────▶│ X:Y₂ │
│ Y:Y₀ │      │ Y:Y₁ │      │ Y:Y₂ │      │ Y:Y₃ │
│XY:h₀ │      │XY:h₁ │      │XY:h₂ │      │XY:h₃ │
└──────┘      └──────┘      └──────┘      └──────┘
```

This is xycore — the open verification protocol. Zero dependencies. Standard library only. Works offline. Works without an account. Works forever. Anyone can implement it. Anyone can verify against it.

pruv is the layer built on xycore. The dashboard, the API, the receipts, the tooling. The protocol belongs to nobody. The layer is the product.

-----

### What proof looks like

Every operation produces a receipt. This one is from an AI agent that modified a codebase.

```
┌─────────────────────────────────────────┐
│                                         │
│  pruv receipt                           │
│                                         │
│  Task:     Fix the login bug            │
│  Agent:    claude-sonnet-4-20250514     │
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

Two lines of code.

```python
from pruv import xy_wrap

wrapped = xy_wrap(my_service)
result = await wrapped.run("Fix the login bug")
```

-----

### Logs are not proof

|        |What you get                                     |What it requires     |
|--------|-------------------------------------------------|---------------------|
|Logs    |"Here's what happened, trust us"                 |Trust in the operator|
|Traces  |"Here's the flow, trust our database"            |Trust in the platform|
|**pruv**|"Here's cryptographic proof — verify it yourself"|Trust in math        |

Logs are assertions. A log entry is a system telling you what it chose to record. It can be modified, deleted, or never written in the first place. A pruv chain cannot be silently altered — any modification breaks verification and reports exactly where.

-----

### Two lines wrap anything

```python
from pruv import xy_wrap

# Any function
@xy_wrap
async def my_workflow(task: str):
    pass

# Any class
wrapped = xy_wrap(my_service)

# Any agent framework
wrapped = xy_wrap(langchain_agent)     # LangChain
wrapped = xy_wrap(crew)                # CrewAI
wrapped = xy_wrap(openai_agent)        # OpenAI Agents
```

No framework opinions. No special integrations. One function wraps anything callable.

-----

### Time travel

Every entry in a pruv chain captures actual state — not what the system logged, not what it reported, but what it cryptographically was at the moment of the operation. The chain is a complete reconstruction of your system at every point it was touched.
Any entry can be opened. State before on the left. State after on the right. The exact change, at the exact moment, syntax-diffed.
Any state can be restored. Not approximately — to the verified cryptographic state as it existed at that entry. If the chain is intact, the restored state is provably identical to the original.

```python
from pruv import CheckpointManager

manager = CheckpointManager(chain, project_dir="./my-project")

checkpoint = manager.create("before-refactor")

# Preview before committing
preview = manager.preview_restore(checkpoint.id)

# Restore to verified state
manager.restore(checkpoint.id)

# Or undo the last action
manager.quick_undo()
```

This changes the economics of mistakes. Recovery is no longer expensive, imprecise, or uncertain. You go back to a verified state you can prove is what you think it is.

-----

### Financial verification

Payments are state transformations. Balance before. Balance after. The conservation law must hold — total in equals total out. pruv enforces this cryptographically at every step.

```python
from pruv import PaymentChain

ledger = PaymentChain("order-7291", api_key="pv_live_...")

ledger.deposit("merchant", 10000.00, source="bank", reference="ACH-4401")

ledger.transfer("merchant", "customer_123", 189.00, reference="pi_3abc")
ledger.transfer("merchant", "customer_456", 64.50, reference="pi_3def")
```

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

Tamper with a single entry — the chain breaks and reports exactly where. Money cannot be created or destroyed silently inside a pruv-wrapped payment system.

Verify the entire ledger in one call:

```python
result = ledger.verify_payments()
# verified_count: 2/2
# all_valid: True
# final_balances: {'merchant': 9746.50, 'customer_123': 189.00, 'customer_456': 64.50}
```

Built for SOX, PCI-DSS, MiFID II. Pair with digital signatures for non-repudiation. Pair with approval gates for multi-signer workflows on high-value transfers.

-----

### Approval gates

High-risk operations pause and wait for a human. Every approval is recorded in the chain — who approved, when, what they approved. Cryptographically signed. Non-repudiable.

```python
wrapped = xy_wrap(
    my_service,
    approval_webhook="https://my-api.com/approve",
    approval_operations=["file.write", "deploy"]
)
```

The system can read all day. The moment it tries to write or deploy, a human approves. The approval is proof, not policy.

-----

### Digital signatures

```python
from xycore import generate_keypair

private_key, public_key = generate_keypair()

wrapped = xy_wrap(my_service, sign=True, private_key=private_key)
```

Ed25519 signatures on every entry. The signer cannot deny they performed the operation. Anyone with the public key verifies independently.

-----

### Architecture scan

Map your entire codebase — services, dependencies, environment variables, connections — derived from source code. No config files. No manual setup.

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

Run it again next week. Diff the two scans. The graph hash changes when your architecture changes. Architecture version control, derived from source.

-----

### Where the layer lives

Any system where state changes and accountability matters. That is not a narrow category.

**AI Agents & Automation** — An agent modifies 40 files, makes 12 API calls, deploys to production. A multi-agent pipeline hands off between three systems. When something goes wrong — or when someone needs to know what happened — the chain shows every action, every state change, every handoff. Independently verifiable. No trust required in the agent, the framework, or the operator.

**Financial Systems** — Money moves between accounts, platforms, and entities. Conservation is enforced cryptographically at every step. Reconciliation is not a manual process — it is a verification call. Auditors do not review logs. They verify chains.

**Operations & Infrastructure** — A deploy pipeline pushes to production. A config change cascades through 14 services. Something breaks. The postmortem does not start with "we think what happened was." It starts with the chain. Exact state at every moment. Rollback to any verified checkpoint.

**Healthcare & Compliance** — A patient record gets modified. A prescription gets filled. A prior authorization gets submitted. Regulators verify independently without access to your systems. The receipt is the audit.

**Supply Chain & Logistics** — Goods move through suppliers, warehouses, customs, carriers, and retailers. Each handoff is a state change with a cryptographic receipt both parties can verify. Disputes resolve against the chain, not against competing claims.

**Legal & Contracts** — A contract moves through drafts, reviews, approvals, and signatures. Every modification is a chain entry. Every approval gate is recorded. The chain is tamper-evident evidence of the document's lifecycle — exportable as proof in a dispute.

**Multi-Party Workflows** — Work crosses organizational boundaries. Each handoff is a trust gap. pruv closes it. Every party verifies what the other parties did without trusting their systems.

-----

### Cloud optional

```python
# Local only — works forever, zero dependencies
from xycore import XYChain
chain = XYChain(name="local")

# Sync to cloud for dashboard, sharing, team features
wrapped = xy_wrap(my_service, api_key="pv_live_...")
```

xycore is the protocol. It has no dependencies, no account requirement, no expiration. It works in air-gapped environments. It works offline. It works forever.

pruv is the layer. The dashboard, the team collaboration, the shareable receipt links, the embeddable badges, the PDF export, the API. The protocol is the foundation. The layer is the product.

-----

### Verify a chain

```python
from pruv import XYChain

chain = XYChain(name="production")
valid, break_index = chain.verify()
```

If valid is True, the chain is intact. Every entry is what it was when it was written. Nobody touched it.

If valid is False, break_index is exactly where the chain was broken. Not approximately. Exactly.

-----

### Install

```bash
pip install xycore    # protocol only, zero dependencies
pip install pruv      # full SDK
```

-----

### Links

- [pruv.dev](https://pruv.dev) — product
- [Dashboard](https://app.pruv.dev) — chain explorer, time travel, receipts
- [Docs](https://docs.pruv.dev) — documentation
- [API Reference](https://api.pruv.dev/docs) — REST API
- [xycore on PyPI](https://pypi.org/project/xycore/) — open protocol
- [pruv on PyPI](https://pypi.org/project/pruv/) — full SDK
- [Follow on X](https://x.com/pruvxy) — @pruvxy

-----

**X → Y → Proof.**
