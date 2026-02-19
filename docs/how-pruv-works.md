# How pruv Works — The Connection Between Everything

This document explains how chains, entries, scans, identities, provenance, API keys, and receipts connect. Read this to understand the full system.

-----

## The Core Primitive: Chains and Entries

Everything in pruv is a **chain**. A chain is an ordered list of **entries**. Each entry captures a state transition:

```
Entry[0]  X = GENESIS           Y = hash(state_after)     XY = proof
Entry[1]  X = Entry[0].Y        Y = hash(state_after)     XY = proof
Entry[2]  X = Entry[1].Y        Y = hash(state_after)     XY = proof
...
Entry[N]  X = Entry[N-1].Y      Y = hash(state_after)     XY = proof
```

**X** is the state before. **Y** is the state after. **XY** is the cryptographic proof that this transition happened. The chain rule is inviolable: every entry's X must equal the previous entry's Y. Break one link, the entire chain after it is untrusted.

This is xycore. Zero dependencies. Works offline. Everything else builds on it.

-----

## How the Pieces Connect

```
                    ┌──────────────┐
                    │   API Keys   │
                    │  pv_live_... │
                    └──────┬───────┘
                           │ authenticates
                           ▼
┌─────────┐         ┌──────────────┐         ┌──────────────┐
│  Scans  │────────▶│    Chains    │◀────────│  Identities  │
└─────────┘ creates └──────┬───────┘ backed  └──────┬───────┘
                           │ contains                │ referenced by
                           ▼                         ▼
                    ┌──────────────┐         ┌──────────────┐
                    │   Entries    │         │  Provenance  │
                    └──────┬───────┘         └──────┬───────┘
                           │ verified by            │ produces
                           ▼                        ▼
                    ┌──────────────┐         ┌──────────────┐
                    │   Receipts   │◀────────│   Receipts   │
                    └──────────────┘         └──────────────┘
```

-----

## Chains

A chain is the fundamental container. Every product in pruv creates chains:

| Product | What the chain records |
|---------|----------------------|
| **Raw chain** | Any sequence of state transitions you define |
| **Identity** | An agent's registration + every action it takes |
| **Provenance** | An artifact's origin + every modification |
| **Scan** | File hashes from a directory or repository |

Chains have:
- A unique ID
- A name
- An ordered list of entries
- Verification status (intact or broken at index N)

```python
import pruv

# Create a raw chain via the API
chain = client.create_chain(name="my-operations")
```

-----

## Entries

An entry is a single state transition inside a chain. Every entry has:

| Field | What it is |
|-------|-----------|
| `index` | Position in the chain (0, 1, 2, ...) |
| `x` | SHA-256 hash of the state before |
| `y` | SHA-256 hash of the state after |
| `xy` | Proof hash: `xy_{sha256(x:operation:y:timestamp)}` |
| `operation` | What happened ("register", "act", "origin", "transition") |
| `x_state` | The full before state (for inspection) |
| `y_state` | The full after state (for inspection) |
| `timestamp` | When it happened |
| `signature` | Optional Ed25519 signature |

The first entry always has `x = "GENESIS"`.

```python
# Entry 0: agent registration
x_state = None                        # didn't exist before
y_state = {"name": "my-agent", ...}   # exists now

# Entry 1: agent action
x_state = {"action_count": 0, ...}    # state before action
y_state = {"action": "read file", ...} # state after action
```

-----

## Identities

An identity is a **chain with semantic meaning**. It represents a persistent, verifiable identity for an AI agent or autonomous system.

**What makes it different from a raw chain:**
- Has an **owner** who is accountable
- Has a declared **scope** of permitted operations
- Has a **validity period** (valid_from / valid_until)
- Has a declared **purpose**
- Every action is checked against the declared scope
- Can be **revoked** (revocation is an entry, not deletion)

**The chain structure:**
```
Entry[0]  operation="register"   → agent comes into existence
Entry[1]  operation="act"        → agent performs an action (in_scope: true/false)
Entry[2]  operation="act"        → another action
...
Entry[N]  operation="revoke"     → agent is revoked (optional)
```

**How to use it:**
```python
import pruv

# Register an agent identity
agent = pruv.identity.register(
    name="deployment-agent",
    framework="crewai",
    owner="your-org",
    scope=["file.read", "file.write", "deploy.production"],
    purpose="Automated production deployments",
    valid_until="2026-12-31"
)

# Record actions (never blocks — records in_scope true/false)
pruv.identity.act(
    agent_id=agent.id,
    action="wrote config to /etc/app/config.yml",
    action_scope="file.write"
)

# Verify — returns full picture, not just true/false
result = pruv.identity.verify(agent.id)
# result.intact, result.active, result.in_scope_count, result.out_of_scope_actions

# Revoke when done
pruv.identity.revoke(agent.id, reason="Project concluded")
```

**Connection to other pieces:**
- Identity is backed by a chain (every identity has a `chain_id`)
- Provenance references identity chains (every artifact transition records which agent did it)
- Receipts pull identity data for accountability

-----

## Provenance

Provenance is a **chain that tracks the origin and custody of a digital artifact**. Every time the artifact is modified, a new entry records who changed it, why, and the before/after content hashes.

**What makes it different from a raw chain:**
- Has an **origin** entry with the artifact's original content hash
- Every transition requires an **agent_id** (links to an identity chain)
- Every transition requires a **reason**
- Verification **cross-checks** the agent's identity chain
- Unauthorized agents (expired, revoked, broken chain) are flagged

**The chain structure:**
```
Entry[0]  operation="origin"      → artifact comes into existence (content hash recorded)
Entry[1]  operation="transition"  → agent modifies artifact (who + why + hash before/after)
Entry[2]  operation="transition"  → another modification
...
```

**How to use it:**
```python
import pruv

# Establish origin
artifact = pruv.provenance.origin(
    content=document_bytes,
    name="legal-contract-v1",
    classification="document",
    owner="your-org"
)

# Record a transition (agent_id + reason required)
pruv.provenance.transition(
    artifact_id=artifact.id,
    updated_content=updated_bytes,
    agent_id=agent.id,          # links to pruv.identity
    reason="Legal review — section 4 revised"
)

# Verify — cross-checks agent identity chains
result = pruv.provenance.verify(artifact.id)
# result.intact, result.transitions, result.unauthorized_transitions
```

**Connection to other pieces:**
- Provenance is backed by a chain
- Each transition references an identity chain via `agent_id`
- Verification pulls and verifies the agent's identity chain
- If an agent's identity chain is broken or revoked, that provenance transition is flagged as unauthorized
- Receipts show the full transition history with agent accountability

-----

## Scans

A scan captures the state of a project directory. It hashes every file and produces a chain with one entry per file.

```python
import pruv

# Scan a directory
graph = pruv.scan("/path/to/project")
# graph.hash — deterministic hash of the entire project state
# graph.files — list of files with their hashes
```

**Connection to other pieces:**
- A scan creates a chain (the file hashes form entries)
- The scan hash can be used as content for provenance (track how a codebase changes over time)

-----

## API Keys

API keys authenticate requests to the pruv API (`api.pruv.dev`).

| Prefix | Environment |
|--------|------------|
| `pv_live_` | Production |
| `pv_test_` | Testing |

**Connection to other pieces:**
- Required for all API operations (creating chains, appending entries, verifying)
- Stored as SHA-256 hashes (the raw key is shown only once at creation)
- Scoped with permissions: `chains:read`, `chains:write`, `entries:read`, etc.
- Rate limited per plan tier

**Dashboard location:** Settings > API Keys

-----

## Receipts

A receipt is the **output of verification**. It proves what happened, who was involved, and whether the record is intact. Every receipt follows the same universal schema:

```json
{
    "pruv_version": "1.0",
    "type": "identity | provenance",
    "chain_id": "...",
    "chain_intact": true,
    "entries": 47,
    "verified": "47/47",
    "X": "hash_before_final_state",
    "Y": "hash_after_final_state",
    "XY": "xy_proof_string",
    "timestamp": "2026-02-19T14:32:11Z",
    "signature": "...",
    "product_data": { ... }
}
```

The `product_data` field carries type-specific content:

| Type | product_data contains |
|------|----------------------|
| **Identity** | agent name, owner, scope, actions total/in-scope, out-of-scope details |
| **Provenance** | artifact name, origin hash, transitions with agent details, unauthorized list |

Every receipt also includes a `human_readable` string — a formatted text version readable by lawyers, regulators, or judges who don't understand cryptography.

**Connection to other pieces:**
- Generated from chains (call `.receipt()` on any product)
- Identity receipts show scope compliance
- Provenance receipts pull identity chains for each agent that touched the artifact
- Exportable as PDF via the API

-----

## The Full Flow — An Example

Here's how everything connects in a real scenario:

### 1. Set up identity
```python
import pruv

# Register the agent that will work on documents
agent = pruv.identity.register(
    name="legal-review-agent",
    framework="langchain",
    owner="legal-team",
    scope=["document.read", "document.edit", "document.review"],
    purpose="Automated legal document review",
    valid_until="2026-12-31"
)
```
*Creates an identity chain. Entry[0] = registration.*

### 2. Establish artifact origin
```python
# Register the document's origin
contract = pruv.provenance.origin(
    content=original_document_bytes,
    name="partnership-agreement-v1",
    classification="document",
    owner="legal-team"
)
```
*Creates a provenance chain. Entry[0] = origin with content hash.*

### 3. Agent works on the document
```python
# Record the agent's action on its identity chain
pruv.identity.act(
    agent_id=agent.id,
    action="Reviewed sections 1-3, added compliance language",
    action_scope="document.edit"
)

# Record the modification on the artifact's provenance chain
pruv.provenance.transition(
    artifact_id=contract.id,
    updated_content=revised_document_bytes,
    agent_id=agent.id,
    reason="Legal review — compliance language added to sections 1-3"
)
```
*Identity chain gets Entry[1] = action. Provenance chain gets Entry[1] = transition with agent reference.*

### 4. Verify everything
```python
# Verify the agent's identity
id_result = pruv.identity.verify(agent.id)
# intact=True, active=True, in_scope_count=1, out_of_scope_actions=[]

# Verify the artifact's provenance (cross-checks agent identity)
prov_result = pruv.provenance.verify(contract.id)
# intact=True, transitions=[{agent: "legal-review-agent", authorized: True}]
```

### 5. Generate receipt
```python
receipt = pruv.provenance.receipt(contract.id)
print(receipt["human_readable"])
```

```
pruv.provenance receipt
─────────────────────────────────────────────

Artifact:       partnership-agreement-v1
Classification: Document
Owner:          legal-team
Origin:         2026-02-19T09:00:00Z

Transitions:    1
Verified:       2/2  ✓
Chain:          intact ✓

─────────────────────────────────────────────

Transition 1    2026-02-19T10:30:00Z
  Agent:        legal-review-agent  ✓
  Owner:        legal-team
  Authorized:   ✓
  Reason:       Legal review — compliance language added to sections 1-3
  State:        [origin] → e5f6a7b8c9d0...

─────────────────────────────────────────────

All transitions verified      ✓
All agents verified           ✓
All agents authorized         ✓
Chain intact                  ✓

─────────────────────────────────────────────

XY:  xy_f3c28e91b4a7...

✓ Verified by pruv
```

-----

## Summary Table

| Concept | What it is | Backed by | References |
|---------|-----------|-----------|------------|
| **Chain** | Ordered list of cryptographically linked entries | xycore | — |
| **Entry** | Single state transition (X → Y with proof XY) | Chain | — |
| **Identity** | Persistent verifiable agent identity | Chain | — |
| **Provenance** | Artifact origin and chain of custody | Chain | Identity (via agent_id) |
| **Scan** | Snapshot of a project directory | Chain | — |
| **API Key** | Authentication for the pruv API | — | — |
| **Receipt** | Verification output readable by anyone | Chain | Identity + Provenance |

The chain is the primitive. Everything else is semantics on top of it.
