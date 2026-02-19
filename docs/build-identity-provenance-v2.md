# pruv.identity & pruv.provenance — Full Implementation Spec

**For Claude Code. Read this entire document before writing a single line of code.**

-----

## Context

pruv is a verification layer built on xycore. xycore is the zero-dependency cryptographic primitive already implemented. Every operation produces an X state before, Y state after, and XY proof the transition happened. Chains are tamper-evident. Verification finds exactly where a chain breaks.

This document specifies the complete implementation of two products:

1. `pruv.identity` — persistent verifiable identity for AI agents and autonomous systems
1. `pruv.provenance` — origin and chain of custody for any digital artifact

These two products must be linked. A provenance chain references the identity chain of every agent that touched the artifact. A receipt that shows what changed, who changed it, whether they were authorized to, and whether the record is intact — that is the output.

Build identity first. Provenance references identity. Do not build them simultaneously.

-----

## Architecture Rules

These rules apply to everything in this document. Do not deviate.

**Rule 1 — xycore handles all cryptography.**
Never reimplement hashing, chaining, or verification. Call xycore. The SDK handles the proof. These products handle the semantics.

**Rule 2 — Universal receipt schema.**
Every product outputs the same receipt structure. Header fields are universal. A `product_data` field carries type-specific content. One receipt format. Always.

**Rule 3 — Identical interface pattern.**
Every product follows the same four methods: `create`, `act`, `verify`, `receipt`. The developer learns it once and understands everything.

**Rule 4 — Receipts must be non-technical readable.**
The cryptographic proof underneath can be as complex as needed. The receipt surface must be legible to a lawyer, regulator, or judge who does not understand cryptography.

**Rule 5 — Verify returns location not just boolean.**
If a chain breaks, verification must report exactly where — which entry, what the state was before and after, who was responsible at that point.

**Rule 6 — Nothing is self-declared.**
Identity is not a claim. It is a chain with an owner, a scope, a validity period, and a purpose declared at registration. Provenance is not a log. It is a cryptographic chain with agent references at every transition.

-----

## Universal Receipt Schema

Define this first. Both products output this structure. Do not modify it per product — use `product_data` for type-specific fields.

```python
{
    "pruv_version": "1.0",
    "type": "identity | provenance",
    "chain_id": str,
    "chain_intact": bool,
    "entries": int,
    "verified": str,          # "47/47" format
    "X": str,                 # state hash before final state
    "Y": str,                 # state hash after final state
    "XY": str,                # xy_... proof string
    "timestamp": str,         # ISO 8601
    "signature": str,
    "product_data": dict      # type-specific — defined per product below
}
```

-----

## Part 1 — pruv.identity

### What It Is

A persistent XY chain attached to an agent. The chain is the identity. Every action the agent takes appends to it. The receipt proves who did what, when, whether it was in scope, across any system, independently verifiable by anyone.

A self-declared name is not identity. Identity requires:

- An owner who is accountable for the agent
- A declared scope of what the agent is permitted to do
- A validity period defining when the identity is active
- A declared purpose
- Every action measured against the declared scope

### File Structure

```
pruv/
  identity/
    __init__.py
    chain.py          # IdentityChain — core XY chain wrapper
    registry.py       # Registration, storage, retrieval
    scope.py          # Scope definition, validation, in-scope checking
    receipt.py        # Receipt generation and formatting
    models.py         # AgentIdentity, IdentityAction, IdentityReceipt dataclasses
```

### Data Models

```python
# models.py

@dataclass
class AgentIdentity:
    id: str                    # uuid4
    name: str                  # human readable agent name
    framework: str             # "crewai" | "langchain" | "openai" | "custom"
    owner: str                 # org or individual identifier — accountable party
    scope: list[str]           # ["file.read", "file.write", "deploy.production"]
    purpose: str               # declared reason this agent exists
    valid_from: str            # ISO 8601
    valid_until: str           # ISO 8601
    chain_id: str              # xycore chain identifier
    created_at: str            # ISO 8601
    status: str                # "active" | "expired" | "revoked"

@dataclass
class IdentityAction:
    agent_id: str
    action: str                # what the agent did
    action_scope: str          # which scope item this maps to
    in_scope: bool             # did this action fall within declared scope
    metadata: dict             # any additional context
    timestamp: str
    entry_index: int           # position in chain

@dataclass
class VerificationResult:
    intact: bool
    entries: int
    verified_count: int
    in_scope_count: int
    out_of_scope_actions: list[IdentityAction]
    break_at: int | None       # entry index where chain breaks, None if intact
    break_detail: dict | None  # state before/after at break point
    active: bool               # is identity within valid_from/valid_until
```

### Registration

```python
# __init__.py — public interface

def register(
    name: str,
    framework: str,
    owner: str,
    scope: list[str],
    purpose: str,
    valid_until: str,
    valid_from: str = None,    # defaults to now
    metadata: dict = None
) -> AgentIdentity:
    """
    First chain entry.
    X state: null — agent did not exist
    Y state: full declared identity as dict
    XY: proof of when this agent came into existence with these properties

    Persists to storage. Returns AgentIdentity.
    """
```

```python
# Registration X/Y states
x_state = None   # agent did not exist

y_state = {
    "name": name,
    "framework": framework,
    "owner": owner,
    "scope": scope,
    "purpose": purpose,
    "valid_from": valid_from,
    "valid_until": valid_until,
    "event": "registration"
}

# Call xycore
entry = chain.append(
    operation="register",
    x_state=x_state,
    y_state=y_state
)
```

### Recording Actions

```python
def act(
    agent_id: str,
    action: str,
    action_scope: str,         # which declared scope item this maps to
    metadata: dict = None
) -> IdentityAction:
    """
    Appends action to identity chain.
    Checks action_scope against declared scope at registration.
    Records in_scope: True/False on the entry.

    X state: current chain state
    Y state: current chain state + this action + in_scope result

    Does NOT block out-of-scope actions — records them.
    The chain is the record. Blocking is the caller's responsibility.
    Detection is pruv's responsibility.
    """
```

```python
# Action X/Y states
x_state = {
    "agent_id": agent_id,
    "previous_action_count": current_entry_count,
    "chain_hash": current_chain_hash
}

in_scope = action_scope in agent.scope

y_state = {
    "agent_id": agent_id,
    "action": action,
    "action_scope": action_scope,
    "in_scope": in_scope,
    "action_count": current_entry_count + 1,
    "metadata": metadata or {},
    "event": "action"
}
```

### Verification

```python
def verify(agent_id: str) -> VerificationResult:
    """
    Verifies entire identity chain.

    Returns:
    - intact: bool — is the chain cryptographically unbroken
    - entries: total entries in chain
    - verified_count: entries that pass verification
    - in_scope_count: actions that were within declared scope
    - out_of_scope_actions: list of actions that fell outside scope
    - break_at: entry index where chain breaks (None if intact)
    - break_detail: X/Y states at break point (None if intact)
    - active: is current time within valid_from/valid_until

    Never returns just True/False.
    Always returns the full picture.
    """
```

### Receipt Generation

```python
def receipt(agent_id: str) -> dict:
    """
    Generates universal receipt for this identity chain.
    Output must be readable by a non-technical party.
    """
```

```python
# product_data for identity receipts
product_data = {
    "agent_name": agent.name,
    "framework": agent.framework,
    "owner": agent.owner,
    "purpose": agent.purpose,
    "scope": agent.scope,
    "valid_from": agent.valid_from,
    "valid_until": agent.valid_until,
    "status": agent.status,
    "actions_total": result.entries - 1,      # subtract registration entry
    "actions_verified": result.verified_count,
    "actions_in_scope": result.in_scope_count,
    "out_of_scope": [
        {
            "action": a.action,
            "attempted_scope": a.action_scope,
            "timestamp": a.timestamp,
            "entry": a.entry_index
        }
        for a in result.out_of_scope_actions
    ],
    "first_seen": agent.created_at,
    "last_action": last_action_timestamp,
    "chain_break": {
        "at_entry": result.break_at,
        "detail": result.break_detail
    } if not result.intact else None
}
```

### Human-Readable Receipt Format

This is what a non-technical party sees. Generate this as a formatted string alongside the JSON receipt.

```
pruv.identity receipt
─────────────────────────────────────────────

Agent:      deployment-agent-prod
Framework:  CrewAI
Owner:      your-org-identifier
Purpose:    Automated production deployments for service X

Scope:
  ✓ file.read
  ✓ file.write
  ✓ deploy.production

Valid:      2026-01-01 → 2026-12-31
Status:     Active

─────────────────────────────────────────────

Actions:    47
Verified:   47/47  ✓
In-scope:   47/47  ✓

Identity chain: intact ✓
First seen:     2026-02-19T09:00:00Z
Last action:    2026-02-19T14:32:11Z

─────────────────────────────────────────────

XY:  xy_a7f3c28e91b4...

✓ Verified by pruv
```

If out-of-scope actions exist:

```
⚠ Out-of-scope actions detected: 2

  Entry 12  2026-02-19T11:22:00Z
  Action:   accessed /etc/passwd
  Attempted scope: system.admin
  Declared scope does not include: system.admin

  Entry 31  2026-02-19T13:45:00Z
  Action:   external API call to unknown endpoint
  Attempted scope: network.external
  Declared scope does not include: network.external
```

If chain is broken:

```
⚠ Chain integrity failure

Break detected at entry 23.
State before entry 23 does not match recorded state.
This chain has been tampered with at or before this point.

Entry 23 timestamp:  2026-02-19T12:01:00Z
Expected X state:    8f3a1c2e...
Found X state:       d4e6f71a...
```

### Revocation

```python
def revoke(agent_id: str, reason: str) -> AgentIdentity:
    """
    Appends revocation entry to chain.
    X state: active identity state
    Y state: revoked identity state + reason
    Updates status to "revoked".
    Chain remains intact and verifiable.
    Revocation is part of the record, not deletion.
    """
```

### Public Interface Summary

```python
import pruv

# Register
agent = pruv.identity.register(
    name="deployment-agent-prod",
    framework="crewai",
    owner="your-org",
    scope=["file.read", "file.write", "deploy.production"],
    purpose="Automated production deployments",
    valid_until="2026-12-31"
)

# Act
pruv.identity.act(
    agent_id=agent.id,
    action="wrote config file to /etc/app/config.yml",
    action_scope="file.write"
)

# Verify
result = pruv.identity.verify(agent.id)

# Receipt
receipt = pruv.identity.receipt(agent.id)

# Revoke
pruv.identity.revoke(agent.id, reason="Project concluded")
```

-----

## Part 2 — pruv.provenance

### What It Is

Origin and chain of custody for any digital artifact. Every artifact has a starting state. Every time it is touched that touch is a state transition. The chain proves what it was at creation, every state it passed through, who touched it at each transition, whether they were authorized, and whether the record is intact.

A provenance chain without agent references proves the artifact changed. It does not prove who changed it or whether they were authorized. This implementation requires agent references.

### File Structure

```
pruv/
  provenance/
    __init__.py
    chain.py          # ProvenanceChain — core XY chain wrapper
    registry.py       # Artifact storage and retrieval
    receipt.py        # Receipt generation and formatting
    models.py         # Artifact, Transition, ProvenanceReceipt dataclasses
```

### Data Models

```python
# models.py

@dataclass
class Artifact:
    id: str                    # uuid4
    name: str                  # human readable artifact name
    classification: str        # "document" | "dataset" | "code" | "model" | "communication" | "custom"
    owner: str                 # who owns this artifact
    chain_id: str              # xycore chain identifier
    origin_hash: str           # hash of original content
    created_at: str            # ISO 8601
    current_state_hash: str    # hash of current content

@dataclass
class Transition:
    artifact_id: str
    agent_id: str              # reference to pruv.identity chain
    agent_name: str            # denormalized for receipt readability
    agent_owner: str           # denormalized for accountability
    agent_in_scope: bool       # was this agent's action within its declared scope
    reason: str                # declared reason for this transition
    content_hash_before: str
    content_hash_after: str
    metadata: dict
    timestamp: str
    entry_index: int

@dataclass
class ProvenanceVerificationResult:
    intact: bool
    entries: int
    verified_count: int
    transitions: list[Transition]
    break_at: int | None
    break_at_agent: str | None      # who was responsible at break point
    break_detail: dict | None
    unauthorized_transitions: list[Transition]   # agent acted outside scope
```

### Establishing Origin

```python
def origin(
    content,                   # bytes, str, dict — the artifact content
    name: str,
    classification: str,
    owner: str,
    metadata: dict = None
) -> Artifact:
    """
    First chain entry. Captures origin state.

    X state: null — artifact did not exist
    Y state: hash of content + artifact metadata
    XY: proof of when this artifact came into existence in this state

    The origin hash is the ground truth.
    Every subsequent transition is measured against it.
    """
```

```python
# Origin X/Y states
content_hash = hash_content(content)   # deterministic hash of artifact content

x_state = None   # artifact did not exist

y_state = {
    "artifact_id": artifact_id,
    "name": name,
    "classification": classification,
    "owner": owner,
    "content_hash": content_hash,
    "metadata": metadata or {},
    "event": "origin"
}
```

### Recording Transitions

```python
def transition(
    artifact_id: str,
    updated_content,           # the artifact after modification
    agent_id: str,             # pruv.identity agent id — required
    reason: str,               # declared reason for this modification — required
    metadata: dict = None
) -> Transition:
    """
    Appends transition to provenance chain.

    Pulls agent identity from pruv.identity to verify:
    - Agent exists and chain is intact
    - Agent is within valid_from/valid_until
    - Agent has not been revoked

    Records agent_in_scope based on agent's own identity verification.

    X state: current content hash + current chain state
    Y state: new content hash + agent reference + reason

    Does NOT block unauthorized transitions.
    Records them. Detection is pruv's responsibility.
    """
```

```python
# Pull agent identity — cross-product reference
agent = pruv.identity.verify(agent_id)

x_state = {
    "artifact_id": artifact_id,
    "content_hash": current_content_hash,
    "transition_count": current_transition_count,
    "chain_hash": current_chain_hash
}

new_content_hash = hash_content(updated_content)

y_state = {
    "artifact_id": artifact_id,
    "content_hash": new_content_hash,
    "agent_id": agent_id,
    "agent_name": agent_name,
    "agent_owner": agent_owner,
    "agent_verified": agent.intact,
    "agent_active": agent.active,
    "agent_in_scope": agent.intact and agent.active,
    "reason": reason,
    "transition_count": current_transition_count + 1,
    "metadata": metadata or {},
    "event": "transition"
}
```

### Verification

```python
def verify(artifact_id: str) -> ProvenanceVerificationResult:
    """
    Verifies entire provenance chain.

    Returns:
    - intact: bool
    - entries: total chain entries
    - verified_count: entries that pass verification
    - transitions: full list of transitions with agent details
    - break_at: entry index where chain breaks
    - break_at_agent: who was responsible at that entry
    - break_detail: X/Y states at break point
    - unauthorized_transitions: transitions where agent was not verified/active/in-scope

    Also cross-verifies each referenced agent identity chain.
    If an agent's identity chain is broken, that transition is flagged.
    """
```

### Receipt Generation

```python
def receipt(artifact_id: str) -> dict:
    """
    Generates universal receipt for this provenance chain.
    Output must be readable by a non-technical party.
    Includes full transition history with agent accountability at each step.
    """
```

```python
# product_data for provenance receipts
product_data = {
    "artifact_name": artifact.name,
    "classification": artifact.classification,
    "owner": artifact.owner,
    "origin_timestamp": artifact.created_at,
    "origin_hash": artifact.origin_hash,
    "current_hash": artifact.current_state_hash,
    "transitions_total": transition_count,
    "transitions_verified": result.verified_count,
    "transitions": [
        {
            "entry": t.entry_index,
            "timestamp": t.timestamp,
            "agent": t.agent_name,
            "agent_owner": t.agent_owner,
            "agent_verified": t.agent_in_scope,
            "reason": t.reason,
            "state_before": t.content_hash_before,
            "state_after": t.content_hash_after
        }
        for t in result.transitions
    ],
    "unauthorized_transitions": [
        {
            "entry": t.entry_index,
            "agent": t.agent_name,
            "reason": t.reason,
            "issue": "agent not verified or outside valid period"
        }
        for t in result.unauthorized_transitions
    ],
    "chain_break": {
        "at_entry": result.break_at,
        "responsible_agent": result.break_at_agent,
        "detail": result.break_detail
    } if not result.intact else None
}
```

### Human-Readable Receipt Format

```
pruv.provenance receipt
─────────────────────────────────────────────

Artifact:       legal-contract-v1
Classification: Document
Owner:          your-org
Origin:         2026-02-19T09:00:00Z

Transitions:    4
Verified:       4/4  ✓
Chain:          intact ✓

─────────────────────────────────────────────

Transition 1    2026-02-19T09:15:00Z
  Agent:        drafting-agent-prod  ✓
  Owner:        your-org
  Authorized:   ✓
  Reason:       Initial draft — sections 1 through 3
  State:        [origin] → a1b2c3d4...

Transition 2    2026-02-19T11:30:00Z
  Agent:        review-agent-legal  ✓
  Owner:        your-org
  Authorized:   ✓
  Reason:       Legal review — section 4 revised, compliance language added
  State:        a1b2c3d4... → e5f6a7b8...

Transition 3    2026-02-19T13:00:00Z
  Agent:        review-agent-legal  ✓
  Owner:        your-org
  Authorized:   ✓
  Reason:       Final edits — signature block added
  State:        e5f6a7b8... → c9d0e1f2...

Transition 4    2026-02-19T14:00:00Z
  Agent:        approval-agent-exec  ✓
  Owner:        your-org
  Authorized:   ✓
  Reason:       Executive approval — document finalized
  State:        c9d0e1f2... → 3a4b5c6d...

─────────────────────────────────────────────

All transitions verified      ✓
All agents verified           ✓
All agents authorized         ✓
Chain intact                  ✓

─────────────────────────────────────────────

XY:  xy_f3c28e91b4a7...

✓ Verified by pruv
```

If tampered:

```
⚠ Chain integrity failure

Break detected at transition 3.
This artifact was tampered with at or before this point.

Transition 3 timestamp:   2026-02-19T13:00:00Z
Responsible agent:        review-agent-legal
Expected state before:    e5f6a7b8...
Found state before:       99aa11bb...

The record of this artifact cannot be trusted from
transition 3 onward. Transitions 1 and 2 are verified intact.
```

### Public Interface Summary

```python
import pruv

# Establish origin
artifact = pruv.provenance.origin(
    content=document_bytes,
    name="legal-contract-v1",
    classification="document",
    owner="your-org"
)

# Record transition — agent_id and reason required
pruv.provenance.transition(
    artifact_id=artifact.id,
    updated_content=updated_document_bytes,
    agent_id=agent.id,
    reason="Legal review — section 4 revised"
)

# Verify
result = pruv.provenance.verify(artifact.id)

# Receipt
receipt = pruv.provenance.receipt(artifact.id)
```

-----

## The Linked Receipt

When both products are implemented, a provenance receipt references identity chains. This is the combined accountability record. It answers all three questions simultaneously:

- **Who** — identity chain proves the agent and its authorization
- **What** — provenance chain proves what artifact was touched and how it changed
- **Whether authorized** — cross-verification between identity scope and provenance transition

No separate call needed. `pruv.provenance.receipt(artifact_id)` automatically pulls and verifies the identity chain for each agent that touched the artifact.

-----

## Storage

Use SQLite via aiosqlite for persistence. Match the pattern already established in XYGLUE.

```
pruv/
  storage/
    identity.db     # agent registrations, actions
    provenance.db   # artifacts, transitions
```

Both databases should be replaceable with any persistent store without changing the product interface. Keep storage behind an abstraction layer.

-----

## Testing Requirements

Write tests for each of the following before considering either product complete.

**Identity tests:**

- Register agent — chain has exactly one entry, X is null
- Act in scope — in_scope is True on entry
- Act out of scope — in_scope is False, action still recorded
- Verify intact chain — returns all counts correct
- Verify broken chain — returns break_at with correct entry index
- Verify expired identity — active is False
- Revoke identity — status updates, chain appends correctly
- Receipt format — all fields present, human readable string generated

**Provenance tests:**

- Origin — chain has exactly one entry, X is null, content hash correct
- Transition with valid agent — agent_in_scope True
- Transition with expired agent — unauthorized_transitions populated
- Transition with revoked agent — unauthorized_transitions populated
- Verify intact chain — all counts correct, all agent references resolve
- Verify broken chain — break_at correct, break_at_agent populated
- Tamper detection — modify stored state, verify catches it at correct entry
- Receipt format — all transitions listed, agent details present, human readable

**Cross-product tests:**

- Provenance receipt pulls identity chain for each agent
- If identity chain is broken, provenance flags that transition as unauthorized
- Revoked agent shows as unauthorized in provenance even if action hash is intact

-----

## What Not To Build

Do not build:

- A UI or dashboard — that comes later
- An API layer — that comes later
- Any of the other three products (contracts, reputation, permissions) — those are roadmap
- Anything that reimplements xycore cryptography
- Any external dependencies beyond what already exists in the pruv repo

Build only what is specified here. Clean interfaces. Complete tests. Readable receipts.

-----

## Completion Criteria

**pruv.identity is complete when:**

- `register`, `act`, `verify`, `receipt`, `revoke` all work
- Verify returns location of break not just boolean
- Out-of-scope actions are detected and reported
- Receipt is legible to a non-technical party
- All identity tests pass

**pruv.provenance is complete when:**

- `origin`, `transition`, `verify`, `receipt` all work
- Every transition requires and records an agent_id
- Every transition requires a reason string
- Verify cross-checks agent identity chains
- Tamper detection reports exact entry and responsible agent
- Receipt shows full transition history with agent accountability
- All provenance tests pass

**Both are complete when:**

- A provenance receipt automatically resolves and displays agent identity for each transition
- A broken identity chain flags the corresponding provenance transition as unauthorized
- The combined receipt answers who, what, and whether authorized in one document

-----

*xycore handles the proof. These products handle the semantics.*
*Build identity first. Provenance references it.*
*Read this entire document before writing a single line of code.*
