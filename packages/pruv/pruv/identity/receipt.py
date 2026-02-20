"""Receipt generation and human-readable formatting for pruv.identity."""

from datetime import datetime, timezone

from .chain import IdentityChain
from .models import AgentIdentity, VerificationResult

FRAMEWORK_DISPLAY_NAMES = {
    "crewai": "CrewAI",
    "langchain": "LangChain",
    "openai": "OpenAI Agents",
    "openclaw": "OpenClaw",
}


def generate_receipt(
    agent: AgentIdentity, chain: IdentityChain, result: VerificationResult
) -> dict:
    """Generate the universal receipt schema for an identity chain.

    Returns a dict with:
    - Universal fields (pruv_version, type, chain_id, etc.)
    - product_data with identity-specific fields
    - human_readable string for non-technical parties
    """
    last_entry = chain.entries[-1] if chain.entries else None

    receipt = {
        "pruv_version": "1.0",
        "type": "identity",
        "chain_id": agent.chain_id,
        "chain_intact": result.intact,
        "entries": result.entries,
        "verified": f"{result.verified_count}/{result.entries}",
        "X": last_entry.x if last_entry else "",
        "Y": last_entry.y if last_entry else "",
        "XY": last_entry.xy if last_entry else "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "signature": last_entry.signature if last_entry else None,
        "product_data": _build_product_data(agent, chain, result),
    }
    receipt["human_readable"] = format_human_readable(agent, result, receipt)
    return receipt


def _build_product_data(
    agent: AgentIdentity, chain: IdentityChain, result: VerificationResult
) -> dict:
    """Build the identity-specific product_data section."""
    # Find last action timestamp
    last_action = None
    for entry in reversed(chain.entries):
        if entry.y_state and entry.y_state.get("event") == "action":
            last_action = entry.y_state.get("timestamp")
            if not last_action:
                last_action = datetime.fromtimestamp(
                    entry.timestamp, tz=timezone.utc
                ).isoformat()
            break

    return {
        "agent_name": agent.name,
        "framework": agent.framework,
        "owner": agent.owner,
        "purpose": agent.purpose,
        "scope": agent.scope,
        "valid_from": agent.valid_from,
        "valid_until": agent.valid_until,
        "status": agent.status,
        "actions_total": result.entries - 1,  # subtract registration entry
        "actions_verified": result.verified_count,
        "actions_in_scope": result.in_scope_count,
        "out_of_scope": [
            {
                "action": a.action,
                "attempted_scope": a.action_scope,
                "timestamp": a.timestamp,
                "entry": a.entry_index,
            }
            for a in result.out_of_scope_actions
        ],
        "first_seen": agent.created_at,
        "last_action": last_action,
        "chain_break": {
            "at_entry": result.break_at,
            "detail": result.break_detail,
        }
        if not result.intact
        else None,
    }


def format_human_readable(
    agent: AgentIdentity, result: VerificationResult, receipt_data: dict
) -> str:
    """Generate the human-readable receipt string.

    This is what a non-technical party (lawyer, regulator, judge) sees.
    """
    sep = "\u2500" * 45
    lines = []

    # Header
    lines.append("pruv.identity receipt")
    lines.append(sep)
    lines.append("")
    framework_display = FRAMEWORK_DISPLAY_NAMES.get(
        agent.framework,
        agent.framework,  # fallback: use raw framework string
    )
    lines.append(f"Agent:      {agent.name}")
    lines.append(f"Framework:  {framework_display}")
    lines.append(f"Owner:      {agent.owner}")
    lines.append(f"Purpose:    {agent.purpose}")
    lines.append("")
    lines.append("Scope:")
    for s in agent.scope:
        lines.append(f"  \u2713 {s}")
    lines.append("")
    lines.append(f"Valid:      {agent.valid_from} \u2192 {agent.valid_until}")
    lines.append(f"Status:     {agent.status.capitalize()}")
    lines.append("")
    lines.append(sep)
    lines.append("")

    # Stats
    actions_total = result.entries - 1
    v_check = "\u2713" if result.verified_count == result.entries else "\u2717"
    lines.append(f"Actions:    {actions_total}")
    lines.append(f"Verified:   {result.verified_count}/{result.entries}  {v_check}")

    scope_check = "\u2713" if result.in_scope_count == actions_total else "\u2717"
    lines.append(f"In-scope:   {result.in_scope_count}/{actions_total}  {scope_check}")
    lines.append("")

    chain_check = "intact \u2713" if result.intact else "BROKEN \u2717"
    lines.append(f"Identity chain: {chain_check}")
    lines.append(f"First seen:     {agent.created_at}")

    pd = receipt_data.get("product_data", {})
    if pd.get("last_action"):
        lines.append(f"Last action:    {pd['last_action']}")

    lines.append("")
    lines.append(sep)
    lines.append("")
    lines.append(f"XY:  {receipt_data.get('XY', '')}")
    lines.append("")

    # Out of scope warnings
    if result.out_of_scope_actions:
        lines.append(
            f"\u26a0 Out-of-scope actions detected: "
            f"{len(result.out_of_scope_actions)}"
        )
        lines.append("")
        for a in result.out_of_scope_actions:
            lines.append(f"  Entry {a.entry_index}  {a.timestamp}")
            lines.append(f"  Action:   {a.action}")
            lines.append(f"  Attempted scope: {a.action_scope}")
            lines.append(f"  Declared scope does not include: {a.action_scope}")
            lines.append("")

    # Chain break warning
    if not result.intact and result.break_at is not None:
        lines.append("\u26a0 Chain integrity failure")
        lines.append("")
        lines.append(f"Break detected at entry {result.break_at}.")
        lines.append("State before entry does not match recorded state.")
        lines.append(
            "This chain has been tampered with at or before this point."
        )
        if result.break_detail:
            lines.append("")
            ts = result.break_detail.get("entry_timestamp")
            if ts:
                lines.append(f"Entry {result.break_at} timestamp:  {ts}")
            lines.append(
                f"Expected X state:    "
                f"{result.break_detail.get('expected_x', 'N/A')}"
            )
            lines.append(
                f"Found X state:       "
                f"{result.break_detail.get('found_x', 'N/A')}"
            )
        lines.append("")

    lines.append("\u2713 Verified by pruv")

    return "\n".join(lines)
