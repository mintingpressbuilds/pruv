"""Receipt generation and human-readable formatting for pruv.provenance."""

from datetime import datetime, timezone

from .chain import ProvenanceChain
from .models import Artifact, ProvenanceVerificationResult


def generate_receipt(
    artifact: Artifact,
    chain: ProvenanceChain,
    result: ProvenanceVerificationResult,
) -> dict:
    """Generate the universal receipt schema for a provenance chain.

    Returns a dict with:
    - Universal fields (pruv_version, type, chain_id, etc.)
    - product_data with provenance-specific fields
    - human_readable string for non-technical parties
    """
    last_entry = chain.entries[-1] if chain.entries else None

    receipt = {
        "pruv_version": "1.0",
        "type": "provenance",
        "chain_id": artifact.chain_id,
        "chain_intact": result.intact,
        "entries": result.entries,
        "verified": f"{result.verified_count}/{result.entries}",
        "X": last_entry.x if last_entry else "",
        "Y": last_entry.y if last_entry else "",
        "XY": last_entry.xy if last_entry else "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "signature": last_entry.signature if last_entry else None,
        "product_data": _build_product_data(artifact, result),
    }
    receipt["human_readable"] = format_human_readable(artifact, result, receipt)
    return receipt


def _build_product_data(
    artifact: Artifact, result: ProvenanceVerificationResult
) -> dict:
    """Build the provenance-specific product_data section."""
    transition_count = len(result.transitions)

    return {
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
                "state_after": t.content_hash_after,
            }
            for t in result.transitions
        ],
        "unauthorized_transitions": [
            {
                "entry": t.entry_index,
                "agent": t.agent_name,
                "reason": t.reason,
                "issue": "agent not verified or outside valid period",
            }
            for t in result.unauthorized_transitions
        ],
        "chain_break": {
            "at_entry": result.break_at,
            "responsible_agent": result.break_at_agent,
            "detail": result.break_detail,
        }
        if not result.intact
        else None,
    }


def format_human_readable(
    artifact: Artifact,
    result: ProvenanceVerificationResult,
    receipt_data: dict,
) -> str:
    """Generate the human-readable receipt string.

    This is what a non-technical party (lawyer, regulator, judge) sees.
    """
    sep = "\u2500" * 45
    lines = []

    # Header
    lines.append("pruv.provenance receipt")
    lines.append(sep)
    lines.append("")
    lines.append(f"Artifact:       {artifact.name}")
    lines.append(f"Classification: {artifact.classification.capitalize()}")
    lines.append(f"Owner:          {artifact.owner}")
    lines.append(f"Origin:         {artifact.created_at}")
    lines.append("")

    transition_count = len(result.transitions)
    v_check = "\u2713" if result.verified_count == result.entries else "\u2717"
    lines.append(f"Transitions:    {transition_count}")
    lines.append(f"Verified:       {result.verified_count}/{result.entries}  {v_check}")

    chain_check = "intact \u2713" if result.intact else "BROKEN \u2717"
    lines.append(f"Chain:          {chain_check}")
    lines.append("")
    lines.append(sep)
    lines.append("")

    # Transition history
    for i, t in enumerate(result.transitions, 1):
        authorized = t.agent_in_scope
        agent_mark = "\u2713" if authorized else "\u2717"
        auth_mark = "\u2713" if authorized else "\u2717"

        lines.append(f"Transition {i}    {t.timestamp}")
        lines.append(f"  Agent:        {t.agent_name}  {agent_mark}")
        lines.append(f"  Owner:        {t.agent_owner}")
        lines.append(f"  Authorized:   {auth_mark}")
        lines.append(f"  Reason:       {t.reason}")

        before = (
            "[origin]" if t.content_hash_before == artifact.origin_hash
            else t.content_hash_before[:12] + "..."
        )
        after = t.content_hash_after[:12] + "..."
        lines.append(f"  State:        {before} \u2192 {after}")
        lines.append("")

    lines.append(sep)
    lines.append("")

    # Summary
    all_verified = result.verified_count == result.entries
    all_agents_verified = all(t.agent_in_scope for t in result.transitions)
    no_unauthorized = len(result.unauthorized_transitions) == 0

    lines.append(
        f"All transitions verified      "
        f"{'✓' if all_verified else '✗'}"
    )
    lines.append(
        f"All agents verified           "
        f"{'✓' if all_agents_verified else '✗'}"
    )
    lines.append(
        f"All agents authorized         "
        f"{'✓' if no_unauthorized else '✗'}"
    )
    lines.append(
        f"Chain intact                  "
        f"{'✓' if result.intact else '✗'}"
    )
    lines.append("")
    lines.append(sep)
    lines.append("")
    lines.append(f"XY:  {receipt_data.get('XY', '')}")
    lines.append("")

    # Unauthorized transitions warning
    if result.unauthorized_transitions:
        lines.append(
            f"\u26a0 Unauthorized transitions detected: "
            f"{len(result.unauthorized_transitions)}"
        )
        lines.append("")
        for t in result.unauthorized_transitions:
            lines.append(f"  Transition at entry {t.entry_index}")
            lines.append(f"  Agent: {t.agent_name}")
            lines.append(f"  Reason: {t.reason}")
            lines.append(
                "  Issue: agent not verified or outside valid period"
            )
            lines.append("")

    # Chain break warning
    if not result.intact and result.break_at is not None:
        lines.append("\u26a0 Chain integrity failure")
        lines.append("")
        lines.append(f"Break detected at transition {result.break_at}.")
        lines.append(
            "This artifact was tampered with at or before this point."
        )
        if result.break_at_agent:
            lines.append(f"Responsible agent:        {result.break_at_agent}")
        if result.break_detail:
            ts = result.break_detail.get("entry_timestamp")
            if ts:
                lines.append(f"Transition timestamp:   {ts}")
            lines.append(
                f"Expected state before:    "
                f"{result.break_detail.get('expected_x', 'N/A')}"
            )
            lines.append(
                f"Found state before:       "
                f"{result.break_detail.get('found_x', 'N/A')}"
            )
        lines.append("")
        # Report which transitions are still trustworthy
        if result.break_at > 1:
            lines.append(
                f"The record of this artifact cannot be trusted from"
            )
            lines.append(
                f"transition {result.break_at} onward. "
                f"Transitions 1 through {result.break_at - 1} are verified intact."
            )
        else:
            lines.append(
                "The record of this artifact cannot be trusted."
            )
        lines.append("")

    lines.append("\u2713 Verified by pruv")

    return "\n".join(lines)
