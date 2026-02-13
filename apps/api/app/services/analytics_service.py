"""Analytics service for the pruv API.

Tracks usage metrics, chain statistics, and provides
dashboards data for the pruv console.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UsageRecord:
    """A single usage record."""
    id: str
    user_id: str
    action: str  # chain.create, entry.append, verify, etc.
    chain_id: str | None = None
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DailyUsage:
    """Aggregated daily usage statistics."""
    date: str  # YYYY-MM-DD
    user_id: str
    entries_created: int = 0
    chains_created: int = 0
    verifications: int = 0
    api_calls: int = 0
    checkpoints_created: int = 0
    receipts_generated: int = 0


class AnalyticsService:
    """Service for tracking and querying usage analytics."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []
        self._daily: dict[str, DailyUsage] = {}  # key: "{date}:{user_id}"

    def track(
        self,
        user_id: str,
        action: str,
        chain_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Track a usage event."""
        record = UsageRecord(
            id=f"evt_{uuid.uuid4().hex[:16]}",
            user_id=user_id,
            action=action,
            chain_id=chain_id,
            metadata=metadata or {},
        )
        self._records.append(record)
        self._update_daily(record)

    def _update_daily(self, record: UsageRecord) -> None:
        """Update daily aggregates."""
        date = time.strftime("%Y-%m-%d", time.gmtime(record.timestamp))
        key = f"{date}:{record.user_id}"

        if key not in self._daily:
            self._daily[key] = DailyUsage(date=date, user_id=record.user_id)

        daily = self._daily[key]
        daily.api_calls += 1

        if record.action == "entry.append" or record.action == "entry.batch":
            count = record.metadata.get("count", 1)
            daily.entries_created += count
        elif record.action == "chain.create":
            daily.chains_created += 1
        elif record.action == "chain.verify":
            daily.verifications += 1
        elif record.action == "checkpoint.create":
            daily.checkpoints_created += 1
        elif record.action == "receipt.generate":
            daily.receipts_generated += 1

    def get_usage_summary(
        self,
        user_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get usage summary for the last N days."""
        cutoff = time.time() - (days * 86400)
        records = [
            r for r in self._records
            if r.user_id == user_id and r.timestamp >= cutoff
        ]

        action_counts: dict[str, int] = defaultdict(int)
        for r in records:
            action_counts[r.action] += 1

        total_entries = sum(
            r.metadata.get("count", 1) for r in records
            if r.action in ("entry.append", "entry.batch")
        )

        return {
            "period_days": days,
            "total_api_calls": len(records),
            "total_entries": total_entries,
            "chains_created": action_counts.get("chain.create", 0),
            "verifications": action_counts.get("chain.verify", 0),
            "checkpoints": action_counts.get("checkpoint.create", 0),
            "receipts": action_counts.get("receipt.generate", 0),
            "action_breakdown": dict(action_counts),
        }

    def get_daily_usage(
        self,
        user_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get daily usage for the last N days."""
        cutoff_date = time.strftime(
            "%Y-%m-%d",
            time.gmtime(time.time() - (days * 86400)),
        )

        daily_records = []
        for key, daily in sorted(self._daily.items()):
            if daily.user_id == user_id and daily.date >= cutoff_date:
                daily_records.append({
                    "date": daily.date,
                    "entries_created": daily.entries_created,
                    "chains_created": daily.chains_created,
                    "verifications": daily.verifications,
                    "api_calls": daily.api_calls,
                    "checkpoints_created": daily.checkpoints_created,
                    "receipts_generated": daily.receipts_generated,
                })

        return daily_records

    def get_monthly_entries(self, user_id: str) -> int:
        """Get total entries created this month."""
        now = time.gmtime()
        month_start = time.strftime("%Y-%m-01", now)

        total = 0
        for key, daily in self._daily.items():
            if daily.user_id == user_id and daily.date >= month_start:
                total += daily.entries_created

        return total

    def get_chain_activity(
        self,
        user_id: str,
        chain_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent activity for a specific chain."""
        records = [
            r for r in self._records
            if r.user_id == user_id and r.chain_id == chain_id
        ]
        records.sort(key=lambda r: r.timestamp, reverse=True)

        return [
            {
                "id": r.id,
                "action": r.action,
                "timestamp": r.timestamp,
                "metadata": r.metadata,
            }
            for r in records[:limit]
        ]

    def get_top_chains(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get the most active chains for a user."""
        chain_counts: dict[str, int] = defaultdict(int)
        chain_latest: dict[str, float] = {}

        for r in self._records:
            if r.user_id == user_id and r.chain_id:
                chain_counts[r.chain_id] += 1
                if r.chain_id not in chain_latest or r.timestamp > chain_latest[r.chain_id]:
                    chain_latest[r.chain_id] = r.timestamp

        sorted_chains = sorted(
            chain_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {
                "chain_id": chain_id,
                "activity_count": count,
                "last_activity": chain_latest.get(chain_id, 0),
            }
            for chain_id, count in sorted_chains[:limit]
        ]

    def get_hourly_distribution(
        self,
        user_id: str,
        days: int = 7,
    ) -> dict[int, int]:
        """Get hourly distribution of API calls."""
        cutoff = time.time() - (days * 86400)
        distribution: dict[int, int] = {h: 0 for h in range(24)}

        for r in self._records:
            if r.user_id == user_id and r.timestamp >= cutoff:
                hour = time.gmtime(r.timestamp).tm_hour
                distribution[hour] += 1

        return distribution


# Global analytics service instance
_analytics_service: AnalyticsService | None = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the global analytics service."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
