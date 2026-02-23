"""Receipt retrieval and formatting for OpenAI Agents integration."""

from __future__ import annotations

from typing import Any


def get_receipt(agent_id: str, client: Any) -> str:
    """Retrieve the identity receipt HTML for an agent."""
    return client.get_identity_receipt(agent_id)


def format_receipt(receipt: dict[str, Any]) -> str:
    """Format a receipt dict as a human-readable text summary."""
    action_count = receipt.get("action_count", 0)
    verified_count = receipt.get("verified_count", action_count)
    in_scope_count = receipt.get("in_scope_count", action_count)
    chain_valid = receipt.get("chain_valid", receipt.get("valid", False))

    lines = [
        "pruv receipt",
        "\u2500" * 45,
        f"Agent:     {receipt.get('name', 'unknown')}",
        f"Framework: {receipt.get('agent_type', 'unknown')}",
        f"Owner:     {receipt.get('owner', 'unknown')}",
        "",
        f"Actions:   {action_count}",
        f"Verified:  {verified_count}/{action_count}",
        f"In scope:  {in_scope_count}/{action_count}",
        "",
        f"Chain:     {'intact \u2713' if chain_valid else 'BROKEN \u2717'}",
        "\u2500" * 45,
        f"XY:  {receipt.get('xy_hash', receipt.get('head_xy', 'unknown'))}",
    ]
    return "\n".join(lines)
