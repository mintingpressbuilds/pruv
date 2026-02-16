# pruv — Homepage Rewrite

## Step 0: AUDIT FIRST

Before changing anything, check what currently exists:

### Dashboard audit

1. Open `apps/dashboard` and read through every page/component
1. Answer: Does the chain explorer timeline exist? Does it show alerts? Can you export? What pages exist?
1. List every existing dashboard page and what it shows

### Docs audit

1. Check if `docs/` has content about the Agent class, integrations, alerting, API reference
1. List what exists and what's missing

### API audit

1. Check `apps/api/app/routes/` for all existing routes
1. List them

**Report findings before proceeding.** Tell me what exists and what's missing.

-----

## Step 1: HOMEPAGE

Location: `apps/web`

### Design language

- Dark. Protocol-spec aesthetic.
- No gradient heroes. No feature cards with icons. No testimonial carousels. No stock images.
- Code is the hero. Real code that works.
- Monospace for code and hashes. Clean sans-serif for body.
- The vibe: technical, minimal, trustworthy, inevitable.
- Reference the existing design in `apps/web` or any `pruv-site.html` in the repo. Match what exists.

-----

### Section 1: Hero

```
pruv

operational proof for any system.

Create a chain. Add entries. Every entry is hashed
and linked to the one before it. Tamper with any entry
and the chain breaks. That's it. That's the protocol.

pip install pruv                              view docs →
```

No image. No illustration. The statement IS the product. The `pip install` is a copyable code block. "view docs" links to docs.pruv.dev.

-----

### Section 2: The protocol in 30 seconds

Live interactive demo. Left side: Python code. Right side: chain building in real-time.

Left:

```python
from pruv import Chain

chain = Chain("invoice-trail")

chain.add("invoice_created", {"id": "INV-0042", "amount": 240.00})
chain.add("payment_received", {"method": "ach", "ref": "TXN-8812"})
chain.add("receipt_issued", {"to": "sarah@company.com"})

chain.verify()
# ✓ 3 entries · chain intact · tamper-proof
```

Right side animates — entries appear one by one with a slight delay:

```
CHAIN: invoice-trail
STATUS: ✓ verified

#1  invoice_created        12:00:01
    hash: a3f8c2e1...

#2  payment_received       12:00:03
    hash: 7d2e9a4f...
    prev: a3f8c2e1...

#3  receipt_issued         12:00:04
    hash: b1c43e7d...
    prev: 7d2e9a4f...

✓ chain intact
   each hash includes the previous hash.
   change any entry and the chain breaks.
```

This is a React client component. Entries appear with 800ms delay between each. Hashes type out character by character. The verification checkmark pulses once when it appears. The connecting lines (│) draw downward.

**Important:** This demo shows a generic business use case (invoicing), NOT an AI agent use case. The protocol is universal. That's the point.

-----

### Section 3: Works everywhere

Show pruv applied across completely different domains. Each one gets a small code snippet showing how natural it is. This is NOT a feature grid with icons. It's real code for real use cases.

Layout: tabbed interface or vertical stack. Each use case is a tab with a code example.

**AI Agents**

```python
agent = pruv.Agent("email-assistant", api_key="pv_live_xxx")

agent.action("read_inbox", {"count": 12})
agent.action("draft_reply", {"to": "sarah@co.com"})
agent.action("send_email", {"to": "sarah@co.com"})

# every action receipted. prove what your agent did.
```

**Payments**

```python
chain = Chain("order-7291")

chain.add("order_placed", {"items": 3, "total": 189.00})
chain.add("payment_authorized", {"method": "card", "last4": "4242"})
chain.add("payment_captured", {"amount": 189.00})
chain.add("fulfillment_started", {"warehouse": "east"})
chain.add("shipped", {"carrier": "fedex", "tracking": "FX882910"})
chain.add("delivered", {"signed_by": "M. Chen"})

# order-to-delivery. every step proven.
```

**Compliance & Audit**

```python
chain = Chain("access-log-2026-02")

chain.add("record_accessed", {
    "user": "dr.patel",
    "record": "patient-8827",
    "reason": "scheduled-appointment"
})

chain.add("record_updated", {
    "user": "dr.patel",
    "field": "prescription",
    "change_hash": "e7f2a1..."  # redacted content, hashed
})

# HIPAA audit trail. cryptographic. immutable.
```

**CI/CD & DevOps**

```python
chain = Chain("deploy-main-4481")

chain.add("commit", {"sha": "a3f8c2e", "author": "kai"})
chain.add("tests_passed", {"suite": "unit", "count": 847, "failures": 0})
chain.add("tests_passed", {"suite": "integration", "count": 124, "failures": 0})
chain.add("build_complete", {"artifact": "app-v2.4.1.tar.gz"})
chain.add("deployed", {"env": "production", "region": "us-east-1"})

# prove the build that went to production. every step.
```

**Supply Chain**

```python
chain = Chain("shipment-LOT-29174")

chain.add("manufactured", {"facility": "shenzhen-03", "batch": "B-441"})
chain.add("qa_passed", {"inspector": "lin.wang", "specs": "ISO-9001"})
chain.add("shipped", {"port": "shenzhen", "vessel": "ever-forward"})
chain.add("customs_cleared", {"port": "long-beach", "docs": "BOL-8827"})
chain.add("received", {"warehouse": "dallas-07", "condition": "intact"})

# field to shelf. every handoff proven.
```

**Legal & Contracts**

```python
chain = Chain("contract-NDA-2026-041")

chain.add("drafted", {"by": "legal@acme.com", "version": 1})
chain.add("reviewed", {"by": "counsel@partner.com", "comments": 3})
chain.add("revised", {"by": "legal@acme.com", "version": 2})
chain.add("signed", {"by": "ceo@acme.com", "method": "docusign"})
chain.add("countersigned", {"by": "ceo@partner.com", "method": "docusign"})
chain.add("executed", {"effective_date": "2026-03-01"})

# chain of custody. every revision. every signature.
```

Each tab/section has a one-line description below the code (the comment at the bottom of each snippet serves this purpose). No paragraph explanations. The code speaks.

-----

### Section 4: The decorator

```
Already have functions? Just decorate them.

import pruv
pruv.init("my-system", api_key="pv_live_xxx")

@pruv.verified
def charge_card(customer_id, amount):
    stripe.charges.create(customer=customer_id, amount=amount)

@pruv.verified
def send_notification(user, message):
    twilio.messages.create(to=user.phone, body=message)

@pruv.verified
def update_record(record_id, data):
    db.records.update(record_id, data)

# every call. every function. automatic receipts.
# zero changes to your existing logic.
```

-----

### Section 5: Framework integrations

```
Plugs into what you already use.
```

Three columns or tabs:

**LangChain**

```python
from pruv.integrations.langchain import PruvCallbackHandler

handler = PruvCallbackHandler(api_key="pv_live_xxx")
agent = initialize_agent(tools, llm, callbacks=[handler])
# every LLM call, tool use, and chain step — receipted.
```

**CrewAI**

```python
from pruv.integrations.crewai import pruv_wrap_crew

verified_crew = pruv_wrap_crew(crew, api_key="pv_live_xxx")
result = verified_crew.kickoff()
# every agent task — receipted.
```

**OpenClaw**

```python
from pruv.integrations.openclaw import OpenClawVerifier

verifier = OpenClawVerifier(api_key="pv_live_xxx")
# every skill execution — receipted.
```

Small text below: `More integrations coming. Any system that performs actions can be verified.`

-----

### Section 6: What happens when something goes wrong

```
Pruv doesn't just record. It watches.
```

Show alert entries appearing one by one (animated):

```
⚠  CRITICAL    Agent accessed .env credentials file
⚠  WARNING     Error rate exceeded 30% (14 of 41 actions failed)
⚠  WARNING     47 actions per minute — unusual volume detected
ℹ  INFO        New external API domain contacted: unknown-service.io
```

Below:

```
Anomaly detection runs on the proof chain itself.
Set severity thresholds. Get webhook alerts.
Your systems can't hide what they did.
```

-----

### Section 7: The receipt

Show a single receipt. This is what pruv produces. Make it feel real and tangible.

```
┌─────────────────────────────────────────────┐
│                                             │
│  RECEIPT                                    │
│                                             │
│  Action:     payment_captured               │
│  Chain:      order-7291                     │
│  Sequence:   #3 of 6                        │
│  Timestamp:  2026-02-15T12:00:03.201Z       │
│                                             │
│  Hash:                                      │
│  b1c43e7d9a4f2b8c1d5e6f7a8b9c0d1e          │
│                                             │
│  Previous:                                  │
│  7d2e9a4f3c8b1d6e5f2a7c4b9d0e8f1a          │
│                                             │
│  ✓ Verified                                 │
│                                             │
│  This receipt is cryptographically linked    │
│  to every entry before it. Tamper with any   │
│  entry and this receipt becomes invalid.     │
│                                             │
└─────────────────────────────────────────────┘
```

Render this as a styled card component. Dark background, subtle border, monospace hashes. The checkmark is green. Optionally: hover the hash and a tooltip shows "SHA-256 of action data + previous hash."

-----

### Section 8: How it works

```
how pruv works

1. Something happens in your system
2. The event data is hashed (SHA-256)
3. The hash includes the previous entry's hash
4. A signed receipt is stored

Each receipt is linked to every receipt before it.
Change any entry in the history and every receipt
after it breaks. Instantly detectable. Unfakeable.

Same principle that secures blockchains.
Without the blockchain.

No tokens. No mining. No gas fees. No consensus.
Just math.
```

This section is text-only. No code. Clean typography. Each numbered step could have a subtle animation or just be static.

The line "Same principle that secures blockchains. Without the blockchain." is the most important line on the entire page. It positions pruv correctly — serious cryptography, not crypto hype.

-----

### Section 9: Install

Centered. Large. Monospace.

```
pip install pruv
```

Copy button. That's the entire section.

Below, three links in a row:

```
docs.pruv.dev              app.pruv.dev              github
documentation              dashboard                 source
```

-----

### Section 10: Footer

```
pruv — operational proof for any system.
```

Links: docs · dashboard · github · api reference · status

Small text: `Built on xycore. Open source.`

-----

## Interactive chain demo component

Location: `apps/web/src/components/ChainDemo.tsx` (or wherever components live)

This is the hero interactive element in Section 2.

```tsx
// State machine:
// 1. Show empty chain panel
// 2. After 500ms: first entry fades in, hash types out
// 3. After 800ms: second entry fades in, "prev" hash connects to first
// 4. After 800ms: third entry fades in
// 5. After 600ms: "✓ chain intact" fades in with green checkmark pulse
// 6. Stay static. User can hover entries to see connections highlighted.

// Each entry card:
// - Sequence number (#1, #2, #3)
// - Action name (bold, white)
// - Timestamp (muted)
// - Hash (monospace, truncated, muted)
// - Prev hash (monospace, truncated, muted) — highlighted same color as previous entry's hash

// The vertical connecting line between entries draws downward during animation

// Colors:
// Background: #0a0a12
// Border: #1a1a24
// Entry dot: white or green
// Action name: #ffffff
// Timestamp: #55556a
// Hash: #55556a, monospace
// Verified checkmark: #22c55e (green)
```

## Use case tabs component

Location: `apps/web/src/components/UseCaseTabs.tsx`

```tsx
// Tab bar with use case names:
// AI Agents | Payments | Compliance | CI/CD | Supply Chain | Legal

// Each tab shows a code block with the relevant snippet
// Code blocks have:
//   - Dark background (#0a0a10)
//   - Subtle border (#1a1a24)
//   - Python syntax highlighting
//   - Copy button top-right
//   - Comment at bottom serves as description (slightly different color)

// Tab transitions: crossfade, 200ms
// Active tab: white text, subtle underline
// Inactive tabs: muted text (#55556a)

// On mobile: horizontal scroll for tabs, or vertical stack
```

## Alert demo component

Location: `apps/web/src/components/AlertDemo.tsx`

```tsx
// 4 alert entries, appear one by one when scrolled into view
// IntersectionObserver triggers the animation
// 500ms delay between each alert appearing
// Animation: fade in + slide from left (12px)

// Alert styling:
// CRITICAL: red icon (⚠), red-tinted text
// WARNING: yellow icon (⚠), yellow-tinted text
// INFO: blue icon (ℹ), blue-tinted text

// Background: transparent or very subtle dark card
// Border-left: 2px solid in alert color
// Monospace for any technical content
```

-----

## Step 2: DASHBOARD FIXES (if needed after audit)

Based on Step 0 findings, add anything missing:

- Chain explorer timeline
- Alerts on chain pages
- API key management
- Navigation updates

Only build what doesn't exist yet.

-----

## Step 3: DOCS UPDATES (if needed after audit)

Add missing doc pages:

1. Quickstart (20 lines to get started)
1. Chain class reference
1. Agent class reference
1. Decorator reference
1. LangChain integration
1. CrewAI integration
1. OpenClaw integration
1. Alerting & webhooks
1. API reference
1. Security & redaction

Only write what doesn't exist yet.

-----

## Acceptance Criteria

### Homepage

- [ ] Hero says "operational proof for any system" — not AI-specific
- [ ] Interactive chain demo shows a generic use case (invoicing), animates correctly
- [ ] 6 use cases shown with real code: AI Agents, Payments, Compliance, CI/CD, Supply Chain, Legal
- [ ] AI Agents is ONE tab among many, not the headline
- [ ] Decorator section shows wrapping regular functions (not just AI)
- [ ] Framework integrations shown (LangChain, CrewAI, OpenClaw)
- [ ] Alert demo shows anomaly detection
- [ ] Receipt card shows what a receipt looks like
- [ ] "How it works" explains chaining simply — mentions "without the blockchain"
- [ ] `pip install pruv` is prominent and copyable
- [ ] Dark theme, protocol-spec aesthetic
- [ ] No stock photos, no illustrations, no gradient heroes, no feature cards with icons
- [ ] Fully responsive on mobile
- [ ] Page loads under 1 second
- [ ] No use of the word "primitive" anywhere on the page

### Dashboard

- [ ] Chain explorer works (if it was missing)
- [ ] Alerts display (if they were missing)

### Docs

- [ ] Quickstart exists
- [ ] All integrations documented
- [ ] API reference complete

## Build order

1. Run the audit (Step 0). Report what exists.
1. Homepage rewrite (Step 1). Priority.
1. Dashboard fixes (Step 2, only what's missing).
1. Docs updates (Step 3, only what's missing).

Execute Step 0 now.
