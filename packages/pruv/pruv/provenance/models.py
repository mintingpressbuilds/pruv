"""Data models for pruv.provenance."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Artifact:
    """A tracked digital artifact with provenance chain."""

    id: str  # uuid4
    name: str  # human readable artifact name
    classification: str  # "document" | "dataset" | "code" | "model" | "communication" | "custom"
    owner: str  # who owns this artifact
    chain_id: str  # xycore chain identifier
    origin_hash: str  # hash of original content
    created_at: str  # ISO 8601
    current_state_hash: str  # hash of current content


@dataclass
class Transition:
    """A single transition in an artifact's provenance chain."""

    artifact_id: str
    agent_id: str  # reference to pruv.identity chain
    agent_name: str  # denormalized for receipt readability
    agent_owner: str  # denormalized for accountability
    agent_in_scope: bool  # was this agent's action within its declared scope
    reason: str  # declared reason for this transition
    content_hash_before: str
    content_hash_after: str
    metadata: dict
    timestamp: str
    entry_index: int


@dataclass
class ProvenanceVerificationResult:
    """Full verification result for a provenance chain."""

    intact: bool
    entries: int
    verified_count: int
    transitions: list[Transition]
    break_at: Optional[int]  # entry index where chain breaks
    break_at_agent: Optional[str]  # who was responsible at break point
    break_detail: Optional[dict]
    unauthorized_transitions: list[Transition]  # agent acted outside scope
