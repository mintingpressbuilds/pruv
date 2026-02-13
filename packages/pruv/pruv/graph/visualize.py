"""Graph visualization utilities for terminal output."""

from __future__ import annotations

from typing import Any

from .graph import Graph, GraphDiff


def format_graph_summary(graph: Graph) -> str:
    """Format a graph summary for terminal display."""
    lines = [
        f"Graph: {graph.root}",
        f"  Hash: {graph.hash}",
        f"  Files: {len(graph.files)}",
        f"  Total lines: {sum(f.get('lines', 0) for f in graph.files)}",
    ]

    # Language breakdown
    langs: dict[str, int] = {}
    for f in graph.files:
        lang = f.get("language", "unknown")
        langs[lang] = langs.get(lang, 0) + 1
    if langs:
        sorted_langs = sorted(langs.items(), key=lambda x: -x[1])
        lang_parts = [f"{name}({count})" for name, count in sorted_langs[:5]]
        lines.append(f"  Languages: {', '.join(lang_parts)}")

    # Frameworks
    if graph.frameworks:
        fw_parts = [
            f"{f['name']}({f.get('confidence', 0):.0%})" for f in graph.frameworks
        ]
        lines.append(f"  Frameworks: {', '.join(fw_parts)}")

    # Services
    if graph.services:
        svc_names = sorted(set(s["name"] for s in graph.services))
        lines.append(f"  Services: {', '.join(svc_names)}")

    # Env vars
    if graph.env_vars:
        env_names = sorted(set(e["name"] for e in graph.env_vars))[:10]
        lines.append(f"  Env vars: {', '.join(env_names)}")

    return "\n".join(lines)


def format_diff(diff: GraphDiff) -> str:
    """Format a graph diff for terminal display."""
    lines = [f"Changes: {diff.summary}"]

    if diff.added:
        lines.append("")
        lines.append("  Added:")
        for change in diff.added[:20]:
            lines.append(f"    + {change.path}")
        if len(diff.added) > 20:
            lines.append(f"    ... and {len(diff.added) - 20} more")

    if diff.removed:
        lines.append("")
        lines.append("  Removed:")
        for change in diff.removed[:20]:
            lines.append(f"    - {change.path}")
        if len(diff.removed) > 20:
            lines.append(f"    ... and {len(diff.removed) - 20} more")

    if diff.modified:
        lines.append("")
        lines.append("  Modified:")
        for change in diff.modified[:20]:
            lines.append(f"    ~ {change.path}")
        if len(diff.modified) > 20:
            lines.append(f"    ... and {len(diff.modified) - 20} more")

    return "\n".join(lines)


def format_chain_timeline(entries: list[dict[str, Any]], width: int = 60) -> str:
    """Format a chain as an ASCII vertical timeline."""
    if not entries:
        return "  (empty chain)"

    lines = []
    for i, entry in enumerate(entries):
        op = entry.get("operation", "unknown")
        status = entry.get("status", "success")
        xy = entry.get("xy", "")[:16]

        # Status indicator
        if status == "success":
            indicator = "●"
        elif status == "failed":
            indicator = "✗"
        else:
            indicator = "○"

        # Entry line
        lines.append(f"  {indicator} [{i}] {op}")
        lines.append(f"  │   xy: {xy}…")

        # Connection line (except last)
        if i < len(entries) - 1:
            lines.append("  │")
            lines.append("  ▼")

    return "\n".join(lines)


def format_entry_detail(entry: dict[str, Any]) -> str:
    """Format a single entry with full detail."""
    lines = [
        f"Entry [{entry.get('index', '?')}]",
        f"  Operation: {entry.get('operation', 'unknown')}",
        f"  Status:    {entry.get('status', 'success')}",
        f"  X:         {entry.get('x', '')[:32]}…",
        f"  Y:         {entry.get('y', '')[:32]}…",
        f"  XY:        {entry.get('xy', '')}",
    ]

    if entry.get("signature"):
        lines.append(f"  Signed:    {entry.get('signer_id', 'unknown')}")
    if entry.get("x_state"):
        lines.append(f"  X State:   {_truncate_dict(entry['x_state'])}")
    if entry.get("y_state"):
        lines.append(f"  Y State:   {_truncate_dict(entry['y_state'])}")

    return "\n".join(lines)


def _truncate_dict(d: dict, max_len: int = 80) -> str:
    """Truncate a dict representation."""
    import json
    s = json.dumps(d, separators=(",", ":"))
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def format_receipt_summary(receipt: dict[str, Any]) -> str:
    """Format a receipt summary."""
    lines = [
        f"Receipt: {receipt.get('id', 'unknown')}",
        f"  Task:      {receipt.get('task', '')}",
        f"  Chain:     {receipt.get('chain_id', '')}",
        f"  Entries:   {receipt.get('entry_count', 0)}",
        f"  Duration:  {receipt.get('duration', 0):.2f}s",
        f"  Verified:  {'✓' if receipt.get('all_verified') else '✗'}",
        f"  Hash:      {receipt.get('hash', receipt.get('receipt_hash', ''))[:32]}…",
    ]
    if receipt.get("agent_type"):
        lines.append(f"  Agent:     {receipt['agent_type']}")
    return "\n".join(lines)
