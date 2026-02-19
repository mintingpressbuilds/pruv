# pruv.identity + pruv.provenance — Build Prompt

## Read first

Read all existing code before writing anything. Understand how these work:

- xycore: XYChain, XYEntry, hash_state, compute_xy, generate_keypair, sign_entry, verify_signature
- pruv: Agent, xy_wrap, PruvClient, PaymentChain
- pruv API: existing chain and entry routes
- pruv dashboard: existing chain explorer and receipt rendering

These two products follow the SAME pattern as everything else in pruv.
A chain is created. Entries are appended. The chain is verified. A receipt
is generated. The difference is semantic — what the chain MEANS, what the
entries REPRESENT, and what the receipt SHOWS.

Do not reinvent chains, entries, or verification. Use what exists.
Add meaning on top.

-----

## The universal interface

Both products follow this pattern. All future pruv products will too.

```python
thing   = pruv.[product].create(...)    # establish
          pruv.[product].act(id, ...)   # operate
result  = pruv.[product].verify(id)     # verify
receipt = pruv.[product].receipt(id)    # export
```

Same four verbs. Every product. A developer learns it once.

-----

# PRODUCT 1: pruv.identity

## What it is

A persistent, verifiable identity for any agent, system, or service.
The identity IS a chain. Every action the agent takes appends to it.
The chain is the complete, tamper-evident history of what that agent
has done. Anyone can verify the identity independently.

## Location

SDK: `packages/pruv/pruv/identity.py`
API: `apps/api/app/routes/identity.py`
Tests: `packages/pruv/tests/test_identity.py`

## SDK Implementation

```python
# pruv/identity.py

"""
pruv.identity — Persistent verifiable identity for agents and systems.

An identity is a chain. Every action appends to it. The chain IS the
identity — not a username, not an API key, not a database row. A
cryptographic chain of everything this agent has done, independently
verifiable by anyone.

Usage:
    import pruv

    # Register an agent identity
    agent = pruv.identity.register(
        name="my-agent",
        agent_type="langchain",
        api_key="pv_live_xxx"
    )

    # Every action is recorded
    pruv.identity.act(agent.id, "read_email", {"from": "boss@co.com"})
    pruv.identity.act(agent.id, "draft_reply", {"to": "boss@co.com"})
    pruv.identity.act(agent.id, "send_email", {"to": "boss@co.com"})

    # Verify the complete identity
    result = pruv.identity.verify(agent.id)
    # 3 actions · all verified · chain intact

    # Export as receipt
    receipt = pruv.identity.receipt(agent.id)
    # Self-verifying HTML — who this agent is, what it did, proof it's real
"""
```

### Update pruv __init__.py

```python
# Add to pruv/__init__.py

from pruv.identity import Identity

class _IdentityProxy:
    """Proxy that initializes Identity on first use."""

    _instance = None

    def register(self, *args, api_key=None, **kwargs):
        if api_key:
            self._instance = Identity(api_key=api_key)
        if not self._instance:
            raise RuntimeError("Call with api_key= on first use")
        return self._instance.register(*args, **kwargs)

    def act(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.act(*args, **kwargs)

    def verify(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.verify(*args, **kwargs)

    def receipt(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.receipt(*args, **kwargs)

    def history(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.history(*args, **kwargs)

identity = _IdentityProxy()
```

This allows: `pruv.identity.register("my-agent", api_key="pv_live_xxx")`

-----

## API Routes for Identity

Location: `apps/api/app/routes/identity.py`

```
POST   /v1/identity/register          Register a new agent identity
POST   /v1/identity/{id}/act          Record an action
GET    /v1/identity/{id}              Get identity details + stats
GET    /v1/identity/{id}/verify       Verify identity chain
GET    /v1/identity/{id}/receipt      Export identity receipt (HTML)
GET    /v1/identity/{id}/history      Get action history
```

### Database

```sql
CREATE TABLE identities (
    id TEXT PRIMARY KEY,              -- pi_ address
    name TEXT NOT NULL,
    agent_type TEXT DEFAULT 'custom',
    public_key TEXT NOT NULL,
    chain_id TEXT NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    action_count BIGINT DEFAULT 0,
    last_action_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_identity_chain ON identities(chain_id);
CREATE INDEX idx_identity_name ON identities(name);
```

-----

## Dashboard: Identity Page

Add to the dashboard navigation: "Identities" link.

### Identity list page: /identities

### Identity detail page: /identities/[id]

- Agent name, type, address, public key
- Action count and timeline (reuses chain explorer component)
- Verification status
- [Verify] [Export Receipt] buttons
- Action history with timestamps

### Register identity page:

- Name input
- Agent type selector (LangChain, CrewAI, OpenAI Agents, Custom)
- After registration: show the identity ID, the code snippet
  for recording actions, and the private key with a warning

-----

# PRODUCT 2: pruv.provenance

## What it is

Origin tracking and chain of custody for any digital artifact —
a document, dataset, image, configuration file, or any piece of data.
The first entry is the origin. Every subsequent entry is a modification.
The chain proves what it was at creation and every state it passed through.

## Location

SDK: `packages/pruv/pruv/provenance.py`
API: `apps/api/app/routes/provenance.py`
Tests: `packages/pruv/tests/test_provenance.py`

### Database

```sql
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,               -- pa_ address
    name TEXT NOT NULL,
    content_hash TEXT NOT NULL,         -- origin hash
    content_type TEXT DEFAULT 'application/octet-stream',
    creator TEXT NOT NULL,
    chain_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    current_hash TEXT NOT NULL,
    transition_count INT DEFAULT 0,
    last_modified_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_artifact_chain ON artifacts(chain_id);
CREATE INDEX idx_artifact_creator ON artifacts(creator);
```

-----

## Build Order

1. pruv.identity SDK — implement Identity class
1. pruv.identity tests — run and pass
1. pruv.identity API routes — wire up endpoints
1. pruv.identity dashboard — identity list + detail + register pages
1. pruv.provenance SDK — implement Provenance class
1. pruv.provenance tests — run and pass
1. pruv.provenance API routes — wire up endpoints
1. pruv.provenance dashboard — artifact list + detail + register pages

Execute in build order. Test each step before moving to the next.
