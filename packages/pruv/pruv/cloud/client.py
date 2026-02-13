"""Cloud client — sync chains to api.pruv.dev with offline queue."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from xycore import XYChain, XYEntry, XYReceipt

API_BASE = "https://api.pruv.dev"


@dataclass
class QueuedRequest:
    """A request queued for later when offline."""

    method: str
    path: str
    body: dict[str, Any]
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "body": self.body,
            "created_at": self.created_at,
        }


class CloudClient:
    """Client for api.pruv.dev with offline queue and retry."""

    def __init__(
        self,
        api_key: str,
        base_url: str = API_BASE,
        queue_dir: str | Path = ".pruv/queue",
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self._offline_queue: list[QueuedRequest] = []

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "pruv-sdk/1.0.0",
        }

    async def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make an API request with retry."""
        import httpx
        url = f"{self.base_url}{path}"
        retries = 0
        while retries <= self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    if method == "GET":
                        resp = await client.get(url, headers=self._headers())
                    elif method == "POST":
                        resp = await client.post(url, headers=self._headers(), json=body)
                    elif method == "PUT":
                        resp = await client.put(url, headers=self._headers(), json=body)
                    else:
                        resp = await client.request(method, url, headers=self._headers(), json=body)

                    if resp.status_code < 400:
                        return resp.json() if resp.content else None
                    elif resp.status_code == 429:
                        retries += 1
                        await _async_sleep(2 ** retries)
                        continue
                    else:
                        return None
            except Exception:
                retries += 1
                if retries > self.max_retries:
                    if body:
                        self._enqueue(method, path, body)
                    return None
                await _async_sleep(2 ** retries)
        return None

    def _enqueue(self, method: str, path: str, body: dict[str, Any]) -> None:
        """Add a request to the offline queue."""
        req = QueuedRequest(method=method, path=path, body=body)
        self._offline_queue.append(req)
        # Persist to disk
        queue_file = self.queue_dir / f"{int(time.time() * 1000)}.json"
        with open(queue_file, "w") as f:
            json.dump(req.to_dict(), f)

    async def flush_queue(self) -> int:
        """Attempt to send all queued requests. Returns number sent."""
        sent = 0
        remaining = []
        for req in self._offline_queue:
            result = await self._request(req.method, req.path, req.body)
            if result is not None:
                sent += 1
            else:
                remaining.append(req)
        self._offline_queue = remaining
        return sent

    async def upload_chain(self, chain: XYChain) -> dict[str, Any] | None:
        """Upload a chain to the cloud."""
        return await self._request("POST", "/v1/chains", chain.to_dict())

    async def append_entry(self, chain_id: str, entry: XYEntry) -> dict[str, Any] | None:
        """Append an entry to a remote chain."""
        return await self._request(
            "POST", f"/v1/chains/{chain_id}/entries", entry.to_dict(),
        )

    async def verify_chain(self, chain_id: str) -> dict[str, Any] | None:
        """Verify a remote chain."""
        return await self._request("GET", f"/v1/chains/{chain_id}/verify")

    async def get_chain(self, chain_id: str) -> dict[str, Any] | None:
        """Get a chain from the cloud."""
        return await self._request("GET", f"/v1/chains/{chain_id}")

    async def list_chains(self) -> dict[str, Any] | None:
        """List all chains."""
        return await self._request("GET", "/v1/chains")

    async def upload_receipt(self, receipt: XYReceipt) -> dict[str, Any] | None:
        """Upload a receipt."""
        return await self._request("POST", f"/v1/receipts", receipt.to_dict())


class CloudStorage:
    """High-level cloud storage that wraps CloudClient."""

    def __init__(self, api_key: str, base_url: str = API_BASE) -> None:
        self.client = CloudClient(api_key=api_key, base_url=base_url)

    async def save(self, chain: XYChain) -> dict[str, Any] | None:
        return await self.client.upload_chain(chain)

    async def load(self, chain_id: str) -> XYChain | None:
        data = await self.client.get_chain(chain_id)
        if data:
            return XYChain.from_dict(data)
        return None

    async def verify(self, chain_id: str) -> bool:
        result = await self.client.verify_chain(chain_id)
        if result:
            return result.get("valid", False)
        return False


async def _async_sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
