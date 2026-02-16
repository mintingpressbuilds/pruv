"""Anomaly detection for agent action chains.

Simple rule-based detection. Not ML. Just rules that catch obvious problems:
  - High error rate (>30% of actions)
  - Unusual action volume (>30 actions/minute)
  - Sensitive file access (.env, credentials, .ssh, etc.)
  - New tool/skill usage after initial tools established
  - New API domain contacted after initial domains established
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    rule: str
    severity: AlertSeverity
    message: str
    chain_id: str
    entry_id: str | None = None
    data: dict[str, Any] | None = None


SENSITIVE_PATHS = (
    ".env", "credentials", "secrets", ".ssh",
    "private", "password", "/etc/shadow",
)


def analyze_chain(chain: dict[str, Any], entries: list[dict[str, Any]]) -> list[Alert]:
    """Run all rules against a chain and return alerts."""
    chain_id = chain["id"]
    alerts: list[Alert] = []

    if not entries:
        return alerts

    alerts.extend(_check_error_rate(chain_id, entries))
    alerts.extend(_check_action_rate(chain_id, entries))
    alerts.extend(_check_new_tools(chain_id, entries))
    alerts.extend(_check_sensitive_files(chain_id, entries))
    alerts.extend(_check_new_domains(chain_id, entries))

    return alerts


# ─── Rule 1: High error rate ─────────────────────────────────────────────────

def _check_error_rate(chain_id: str, entries: list[dict[str, Any]]) -> list[Alert]:
    total = len(entries)
    if total <= 5:
        return []

    errors = [
        e for e in entries
        if ".error" in e.get("operation", "") or "error" in e.get("operation", "").lower()
    ]
    error_count = len(errors)

    if error_count / total > 0.3:
        return [Alert(
            rule="high_error_rate",
            severity=AlertSeverity.WARNING,
            message=f"Error rate is {error_count}/{total} ({error_count / total:.0%})",
            chain_id=chain_id,
        )]
    return []


# ─── Rule 2: Unusual action volume ───────────────────────────────────────────

def _check_action_rate(chain_id: str, entries: list[dict[str, Any]]) -> list[Alert]:
    if len(entries) <= 100:
        return []

    first_ts = entries[0].get("timestamp", 0)
    last_ts = entries[-1].get("timestamp", 0)

    # Also check metadata.ts if timestamps are epoch
    if not first_ts:
        first_ts = _get_nested_ts(entries[0])
    if not last_ts:
        last_ts = _get_nested_ts(entries[-1])

    duration = last_ts - first_ts
    if duration <= 0:
        return []

    rate = len(entries) / (duration / 60)  # actions per minute
    if rate > 30:
        return [Alert(
            rule="high_action_rate",
            severity=AlertSeverity.WARNING,
            message=f"Agent performing {rate:.0f} actions/minute",
            chain_id=chain_id,
        )]
    return []


# ─── Rule 3: New tool/skill usage ────────────────────────────────────────────

def _check_new_tools(chain_id: str, entries: list[dict[str, Any]]) -> list[Alert]:
    alerts: list[Alert] = []
    tools_seen: set[str] = set()

    for entry in entries:
        operation = entry.get("operation", "")
        if "tool.start" not in operation and "skill.start" not in operation:
            continue

        # Extract tool name from metadata or y_state
        tool_name = _extract_tool_name(entry)
        if not tool_name:
            continue

        if tool_name not in tools_seen and len(tools_seen) > 3:
            alerts.append(Alert(
                rule="new_tool",
                severity=AlertSeverity.INFO,
                message=f"Agent used new tool: {tool_name}",
                chain_id=chain_id,
                entry_id=entry.get("id"),
            ))
        tools_seen.add(tool_name)

    return alerts


# ─── Rule 4: Sensitive file access ───────────────────────────────────────────

def _check_sensitive_files(chain_id: str, entries: list[dict[str, Any]]) -> list[Alert]:
    alerts: list[Alert] = []

    for entry in entries:
        operation = entry.get("operation", "")
        if "file.access" not in operation:
            continue

        path = _extract_field(entry, "path")
        if not path:
            continue

        path_lower = path.lower()
        for sensitive in SENSITIVE_PATHS:
            if sensitive in path_lower:
                alerts.append(Alert(
                    rule="sensitive_file_access",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Agent accessed sensitive file: {path}",
                    chain_id=chain_id,
                    entry_id=entry.get("id"),
                ))
                break

    return alerts


# ─── Rule 5: New API domains ─────────────────────────────────────────────────

def _check_new_domains(chain_id: str, entries: list[dict[str, Any]]) -> list[Alert]:
    alerts: list[Alert] = []
    known_domains: set[str] = set()

    for entry in entries:
        operation = entry.get("operation", "")
        if "api.call" not in operation:
            continue

        url = _extract_field(entry, "url")
        if not url:
            continue

        domain = _extract_domain(url)
        if not domain:
            continue

        if domain not in known_domains and len(known_domains) > 2:
            alerts.append(Alert(
                rule="new_api_domain",
                severity=AlertSeverity.INFO,
                message=f"Agent contacted new domain: {domain}",
                chain_id=chain_id,
                entry_id=entry.get("id"),
            ))
        known_domains.add(domain)

    return alerts


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def _get_nested_ts(entry: dict[str, Any]) -> float:
    """Try to get timestamp from nested metadata."""
    meta = entry.get("metadata") or {}
    return meta.get("ts", 0) or meta.get("timestamp", 0)


def _extract_tool_name(entry: dict[str, Any]) -> str:
    """Extract tool/skill name from entry metadata or y_state."""
    meta = entry.get("metadata") or {}
    name = meta.get("tool") or meta.get("skill") or ""
    if name:
        return name

    # Try nested data
    data = meta.get("data") or {}
    name = data.get("tool") or data.get("skill") or ""
    if name:
        return name

    # Try y_state
    y_state = entry.get("y_state") or {}
    return y_state.get("tool") or y_state.get("skill") or ""


def _extract_field(entry: dict[str, Any], field_name: str) -> str:
    """Extract a field from entry metadata or y_state."""
    meta = entry.get("metadata") or {}
    val = meta.get(field_name) or ""
    if val:
        return val

    data = meta.get("data") or {}
    val = data.get(field_name) or ""
    if val:
        return val

    y_state = entry.get("y_state") or {}
    return y_state.get(field_name) or ""
