"""Data models for pruv.identity."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentIdentity:
    """A persistent verifiable identity for an AI agent."""

    id: str  # uuid4
    name: str  # human readable agent name
    framework: str  # "crewai" | "langchain" | "openai" | "openclaw" | "custom"
    owner: str  # org or individual identifier — accountable party
    scope: list[str]  # ["file.read", "file.write", "deploy.production"]
    purpose: str  # declared reason this agent exists
    valid_from: str  # ISO 8601
    valid_until: str  # ISO 8601
    chain_id: str  # xycore chain identifier
    created_at: str  # ISO 8601
    status: str = "active"  # "active" | "expired" | "revoked"


@dataclass
class IdentityAction:
    """A single action recorded on an identity chain."""

    agent_id: str
    action: str  # what the agent did
    action_scope: str  # which scope item this maps to
    in_scope: bool  # did this action fall within declared scope
    metadata: dict  # any additional context
    timestamp: str
    entry_index: int  # position in chain


@dataclass
class VerificationResult:
    """Full verification result for an identity chain."""

    intact: bool
    entries: int
    verified_count: int
    in_scope_count: int
    out_of_scope_actions: list[IdentityAction]
    break_at: Optional[int]  # entry index where chain breaks, None if intact
    break_detail: Optional[dict]  # state before/after at break point
    active: bool  # is identity within valid_from/valid_until


# Recommended scope vocabulary for OpenClaw agents, grouped by category.
# OpenClaw runs with broad system-level permissions — these
# scope values map to what OpenClaw agents actually do on
# a user's machine. Use these when registering OpenClaw agents
# to enable precise in-scope checking on every action.
#
# The grouped dict is the source of truth. The flat list is
# derived from it so existing code that imports OPENCLAW_SCOPE_OPTIONS
# keeps working unchanged.

OPENCLAW_SCOPE_GROUPS: dict[str, list[str]] = {
    "File System": [
        "file.read",
        "file.write",
        "file.delete",
    ],
    "Email": [
        "email.read",
        "email.send",
    ],
    "Calendar": [
        "calendar.read",
        "calendar.write",
    ],
    "Browser": [
        "browser.read",
        "browser.interact",
    ],
    "System": [
        "system.execute",
        "network.external",
    ],
    "Messaging": [
        "messaging.read",
        "messaging.send",
    ],
}

# Flat list derived from groups — backwards compatible
OPENCLAW_SCOPE_OPTIONS = [
    scope
    for scopes in OPENCLAW_SCOPE_GROUPS.values()
    for scope in scopes
]
