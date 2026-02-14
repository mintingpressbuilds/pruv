"""Offline queue for cloud sync with persistent storage and retry logic."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class QueueItem:
    """An item in the offline queue."""

    id: str
    method: str
    path: str
    body: dict[str, Any]
    created_at: float
    attempts: int = 0
    last_attempt: float = 0.0
    max_retries: int = 5

    @property
    def should_retry(self) -> bool:
        """Check if this item should be retried."""
        if self.attempts >= self.max_retries:
            return False
        # Exponential backoff: 2^attempts seconds
        if self.last_attempt > 0:
            backoff = min(2 ** self.attempts, 300)  # Max 5 minutes
            if time.time() - self.last_attempt < backoff:
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "method": self.method,
            "path": self.path,
            "body": self.body,
            "created_at": self.created_at,
            "attempts": self.attempts,
            "last_attempt": self.last_attempt,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueueItem":
        return cls(
            id=data["id"],
            method=data["method"],
            path=data["path"],
            body=data["body"],
            created_at=data["created_at"],
            attempts=data.get("attempts", 0),
            last_attempt=data.get("last_attempt", 0.0),
            max_retries=data.get("max_retries", 5),
        )


class OfflineQueue:
    """Persistent offline queue for cloud requests.

    Stores failed requests to disk and retries them
    when connectivity is restored.
    """

    def __init__(self, queue_dir: str | Path = ".pruv/queue") -> None:
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self._items: list[QueueItem] = []
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load queued items from disk."""
        for path in sorted(self.queue_dir.glob("*.json")):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                self._items.append(QueueItem.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue

    def enqueue(self, item: QueueItem) -> None:
        """Add an item to the queue and persist to disk."""
        self._items.append(item)
        self._save_item(item)

    def dequeue(self) -> QueueItem | None:
        """Get the next retryable item from the queue."""
        for item in self._items:
            if item.should_retry:
                return item
        return None

    def mark_sent(self, item_id: str) -> None:
        """Remove a successfully sent item."""
        self._items = [i for i in self._items if i.id != item_id]
        self._delete_item(item_id)

    def mark_failed(self, item_id: str) -> None:
        """Mark an item as failed (increment attempt counter)."""
        for item in self._items:
            if item.id == item_id:
                item.attempts += 1
                item.last_attempt = time.time()
                self._save_item(item)
                break

    def get_pending(self) -> list[QueueItem]:
        """Get all pending items."""
        return [i for i in self._items if i.should_retry]

    def get_dead_letters(self) -> list[QueueItem]:
        """Get items that have exceeded max retries."""
        return [i for i in self._items if not i.should_retry]

    def clear(self) -> int:
        """Clear all items. Returns count cleared."""
        count = len(self._items)
        for item in self._items:
            self._delete_item(item.id)
        self._items.clear()
        return count

    @property
    def size(self) -> int:
        return len(self._items)

    @property
    def pending_count(self) -> int:
        return len(self.get_pending())

    def _save_item(self, item: QueueItem) -> None:
        """Persist an item to disk."""
        path = self.queue_dir / f"{item.id}.json"
        with open(path, "w") as f:
            json.dump(item.to_dict(), f, indent=2)

    def _delete_item(self, item_id: str) -> None:
        """Delete an item from disk."""
        path = self.queue_dir / f"{item_id}.json"
        if path.exists():
            os.remove(path)

    def summary(self) -> dict[str, Any]:
        """Get a summary of the queue state."""
        return {
            "total": len(self._items),
            "pending": self.pending_count,
            "dead_letters": len(self.get_dead_letters()),
        }
