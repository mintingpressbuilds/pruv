# pruv — Homepage + Dashboard + Docs Audit

## Step 0: AUDIT FIRST

Before changing anything, check what currently exists:

### Dashboard audit

1. Open `apps/dashboard` and read through every page/component
1. Answer these questions:
- Does the chain explorer timeline exist? (from PRUV_AGENT_BUILD.md Section 3)
- Does it show agent actions as a visual timeline?
- Does it show alerts/anomalies?
- Does it show verification status with a checkmark?
- Can you click an action to expand details?
- Can you export a chain?
- Is there an API keys management page?
- What pages/routes currently exist?
1. List every existing dashboard page and what it shows

### Docs audit

1. Check if `docs/` folder has content about:
- The Agent class and @pruv.verified decorator
- LangChain / CrewAI / OpenClaw integrations
- The alerting system
- Chain explorer usage
1. List what docs exist and what's missing

### API audit

1. Check `apps/api/app/routes/` for:
- Chain alerts endpoint (/v1/chains/{id}/alerts)
- Agent-related endpoints
1. List what routes exist

**Report findings before proceeding to Step 1.** Tell me exactly what exists and what's missing so we know what the homepage can honestly claim.

-----

## Step 1: HOMEPAGE REWRITE

Location: `apps/web`

The homepage must communicate one thing instantly: **pruv proves what your AI agent did.**

Not "verification API." Not "cryptographic chain." Not technical jargon. A developer lands on this page and understands in 5 seconds what pruv does and why they need it.

### Design language

- Dark. Protocol-spec aesthetic.
- No gradient heroes. No feature cards with icons. No testimonial carousels.
- Code is the hero. Show real code that works.
- Monospace for code and hashes. Instrument Sans or similar for body.
- The vibe is: technical, minimal, trustworthy, serious.

### Page structure

**Section 1: Hero**

```
pruv

prove what your AI agent did.

Every action. Every tool call. Every message.
Cryptographic receipts your agent can't fake.

[pip install pruv]                    [view docs →]
```

No image. No illustration. Just the statement. The code install command IS the call to action.

**Section 2: The problem (2 sentences max)**

```
AI agents read your email, send messages, execute code,
and access your files. You have no proof of what they actually did.

Logs can be edited. Logs can be deleted. Logs lie.
Pruv receipts are cryptographic. They can't.
```

**Section 3: Live code demo**

The centerpiece of the homepage. Real Python code that actually works. Not pseudocode.

Left side: the code. Right side: the chain output (animated, entries appear one by one).

```python
import pruv

agent = pruv.Agent("email-assistant", api_key="pv_live_xxx")

agent.action("read_inbox", {"account": "work", "count": 12})
agent.action("draft_reply", {"to": "sarah@company.com"})
agent.action("send_email", {"to": "sarah@company.com", "subject": "Re: Q3"})

chain = agent.verify()
# ✓ 3 actions · all verified · chain intact
```

Right side shows the chain building in real-time:

```
CHAIN: email-assistant-1739644800
STATUS: ✓ verified

#1  read_inbox           12:00:01.003
    hash: a3f8c2e1...

#2  draft_reply          12:00:02.847
    hash: 7d2e9a4f...
    prev: a3f8c2e1...

#3  send_email           12:00:03.201
    hash: b1c43e7d...
    prev: 7d2e9a4f...

Chain integrity: ✓ intact
Each hash includes the previous hash.
Tamper with any entry and the chain breaks.
```

This should be an interactive React component. The code appears with a typing effect or is static. The chain output animates — entries appear one by one with a slight delay, hashes fade in, the verification checkmark appears at the end.

**Section 4: The decorator (even simpler)**

```
Or just decorate your existing functions.
Zero code changes to your logic.

@pruv.verified
def send_email(to, subject, body):
    smtp.send(to, subject, body)

# Every call to send_email now has
# a cryptographic receipt. Automatically.
```

**Section 5: Framework integrations**

```
Works with the tools you already use.

LangChain    CrewAI    OpenClaw
```

Each one shows a 3-line code snippet:

LangChain:

```python
from pruv.integrations.langchain import PruvCallbackHandler
handler = PruvCallbackHandler(api_key="pv_live_xxx")
agent = initialize_agent(tools, llm, callbacks=[handler])
```

CrewAI:

```python
from pruv.integrations.crewai import pruv_wrap_crew
crew = pruv_wrap_crew(crew, api_key="pv_live_xxx")
result = crew.kickoff()
```

OpenClaw:

```python
from pruv.integrations.openclaw import OpenClawVerifier
verifier = OpenClawVerifier(api_key="pv_live_xxx")
# Every skill execution is now verified
```

Three tabs or three columns. Click to switch between them.

**Section 6: What pruv catches**

```
Pruv doesn't just record. It watches.

⚠ Agent accessed .env file
⚠ Error rate exceeded 30%
⚠ Agent contacted unknown API domain
⚠ 47 actions per minute (unusual volume)

Anomaly detection on the proof chain itself.
Your agent can't hide what it did.
```

Show these as alert-style entries, maybe with a subtle animation where they appear one by one.

**Section 7: The receipt**

Show what a pruv receipt actually looks like. A single receipt card:

```
┌─────────────────────────────────────┐
│  RECEIPT                            │
│                                     │
│  Action:    send_email              │
│  Sequence:  #3 of 47               │
│  Timestamp: 2026-02-15T12:00:03Z   │
│                                     │
│  Hash:                              │
│  b1c43e7d9a4f2b8c1d5e6f7a8b9c0d1e │
│                                     │
│  Previous:                          │
│  7d2e9a4f3c8b1d6e5f2a7c4b9d0e8f1a │
│                                     │
│  ✓ Verified                         │
│  This receipt is cryptographically  │
│  linked to every action before it.  │
│  Tamper with any entry and this     │
│  receipt becomes invalid.           │
└─────────────────────────────────────┘
```

This could be an interactive element — hover over the hash and it highlights the connection to the previous entry. Or just a static, beautiful card.

**Section 8: How it works (technical, for the curious)**

```
How pruv works

1. Your agent performs an action
2. The action data is hashed (SHA-256)
3. The hash is chained to the previous hash
4. A signed receipt is stored

Each receipt contains the hash of the previous receipt.
Change any action in the history and every receipt after it breaks.
This is the same principle that secures blockchains —
without the blockchain.

No tokens. No mining. No gas fees. Just math.
```

Short. Technical but accessible. The "without the blockchain" line is important — it preempts the "why not just use a blockchain" question.

**Section 9: Install**

```
pip install pruv
```

Big. Centered. Monospace. That's the entire section. Maybe a copy button.

Below it:

```
docs.pruv.dev          app.pruv.dev          github.com/xxx/pruv
documentation          dashboard              source code
```

**Section 10: Footer**

```
pruv — prove what your AI agent did.

Built on xycore. Open source.
```

Minimal. Link to GitHub. Link to docs.

-----

### Interactive chain demo component

Location: `apps/web/src/components/ChainDemo.tsx`

This is the hero component. A React client component that shows a simulated chain building.

```tsx
// ChainDemo.tsx

// State: array of chain entries that appear one by one
// On mount (or when scrolled into view): start the animation
// Each entry appears after 800ms delay
// Entry animation: fade in + slide up
// Hash text types out character by character (fast, 50ms per char)
// After all entries: verification checkmark appears with a subtle pulse
// The chain lines (│) connecting entries animate downward

// Data (hardcoded — this is a demo, not a live API call):
const DEMO_ENTRIES = [
  { seq: 1, action: "read_inbox", time: "12:00:01", hash: "a3f8c2e1b7d4..." },
  { seq: 2, action: "draft_reply", time: "12:00:02", hash: "7d2e9a4f3c8b..." },
  { seq: 3, action: "send_email", time: "12:00:03", hash: "b1c43e7d9a4f..." },
];

// Style: dark card with subtle border, monospace text
// Green dots for each entry
// Muted gray for timestamps and hashes
// White for action names
// Green checkmark at the end
```

### Code block component

Reusable component for showing Python code with syntax highlighting:

```tsx
// CodeBlock.tsx

// Dark background (#0a0a10)
// Subtle border (#1a1a24)
// Python syntax highlighting (keywords, strings, comments in different colors)
// Copy button top-right
// Language label top-left ("python")
// Monospace font (JetBrains Mono or similar)
```

### Alert demo component

For Section 6:

```tsx
// AlertDemo.tsx

// Shows 4 alert entries appearing one by one
// Each has a warning icon (⚠) in yellow/red
// Slight delay between each (600ms)
// Fade in + slide right animation
// Color-coded: yellow for warning, red for critical
```

-----

## Step 2: DASHBOARD UPDATES (if needed)

Based on the audit in Step 0, update the dashboard to include anything missing:

### Chain explorer (if not built yet)

- Add `/chains/[id]` page with visual timeline
- See PRUV_AGENT_BUILD.md Section 3 for full spec

### Alerts panel (if not built yet)

- Show alerts inline on chain explorer
- Summary badge at top of chain page

### API keys page (if not built yet)

- Create/revoke API keys
- Show usage stats per key
- Copy key to clipboard

### Navigation

Sidebar or top nav should include:

- Chains (list all chains)
- API Keys
- Docs link (external → docs.pruv.dev)
- Account/settings

-----

## Step 3: DOCS UPDATES (if needed)

Based on the audit in Step 0, add any missing documentation:

### Required doc pages:

1. **Quickstart** — pip install, create agent, record 3 actions, verify. Under 20 lines of code.
1. **Agent class reference** — all methods, parameters, return types.
1. **Decorator reference** — @pruv.verified usage, with and without options.
1. **LangChain integration** — install, setup, what gets recorded, example.
1. **CrewAI integration** — same format.
1. **OpenClaw integration** — same format.
1. **Chain explorer** — how to use the dashboard to view chains.
1. **Alerting** — what rules exist, how to configure webhooks, severity levels.
1. **Security** — how redaction works, what data is stored, what's hashed.
1. **API reference** — all endpoints, request/response formats.

-----

## Acceptance Criteria

### Homepage

- [ ] Hero communicates "prove what your AI agent did" in under 5 seconds
- [ ] Live chain demo animates correctly (entries appear, hashes type out, verification appears)
- [ ] Code examples are real, working Python code
- [ ] All three framework integrations shown with code snippets
- [ ] Alert demo shows anomaly detection
- [ ] Receipt card shows what a receipt looks like
- [ ] "How it works" explains the chain without jargon
- [ ] `pip install pruv` is prominent and copyable
- [ ] Page is fully responsive on mobile
- [ ] Dark theme, protocol-spec aesthetic, no generic SaaS design
- [ ] No stock photos, no illustrations, no gradient heroes
- [ ] Page loads under 1 second
- [ ] Design matches the existing pruv design language (check the reference HTML if it exists)

### Dashboard

- [ ] Chain explorer shows visual timeline (if it was missing)
- [ ] Alerts display on chain pages (if they were missing)
- [ ] API keys manageable from dashboard

### Docs

- [ ] Quickstart exists and works in under 20 lines
- [ ] All integrations documented
- [ ] Alerting documented
- [ ] API reference complete

## Build order

1. Run the audit (Step 0). Report what exists.
1. Homepage rewrite (Step 1). This is the priority.
1. Dashboard fixes (Step 2, only what's missing).
1. Docs updates (Step 3, only what's missing).

Execute Step 0 now. Report findings before building anything.
