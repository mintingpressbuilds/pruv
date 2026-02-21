"""Synchronous HTTP client for the pruv API."""

from __future__ import annotations

from typing import Any

import httpx


class PruvClient:
    """Synchronous HTTP client for api.pruv.dev.

    Used by the Agent class for simple, blocking API calls.
    For async usage, see CloudClient in pruv.cloud.

    Usage:
        client = PruvClient(api_key="pv_live_xxx")
        chain = client.create_chain("my-chain")
        client.add_entry(chain["id"], {"action": "test"})
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self._http = httpx.Client(
            base_url=self.endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "pruv-sdk/1.0.1",
            },
            timeout=30.0,
        )

    def create_chain(
        self, name: str, metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = self._http.post("/v1/chains", json={
            "name": name,
            "metadata": metadata or {},
        })
        resp.raise_for_status()
        return resp.json()

    def add_entry(self, chain_id: str, data: dict[str, Any]) -> dict[str, Any]:
        resp = self._http.post(f"/v1/chains/{chain_id}/entries", json={
            "data": data,
        })
        resp.raise_for_status()
        return resp.json()

    def get_chain(self, chain_id: str) -> dict[str, Any]:
        resp = self._http.get(f"/v1/chains/{chain_id}")
        resp.raise_for_status()
        return resp.json()

    def get_entry(self, chain_id: str, entry_id: str) -> dict[str, Any]:
        resp = self._http.get(
            f"/v1/chains/{chain_id}/entries/{entry_id}",
        )
        resp.raise_for_status()
        return resp.json()

    def verify_chain(self, chain_id: str) -> dict[str, Any]:
        resp = self._http.get(f"/v1/chains/{chain_id}/verify")
        resp.raise_for_status()
        return resp.json()

    def export_chain(self, chain_id: str) -> str:
        resp = self._http.get(f"/v1/chains/{chain_id}/export")
        resp.raise_for_status()
        return resp.text

    def list_chains(
        self, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        resp = self._http.get("/v1/chains", params={
            "limit": limit,
            "offset": offset,
        })
        resp.raise_for_status()
        return resp.json()

    # ── Identity endpoints ──

    def register_identity(
        self,
        name: str,
        agent_type: str = "custom",
        owner: str = "",
        scope: list[str] | None = None,
        purpose: str = "",
        valid_from: str | None = None,
        valid_until: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "agent_type": agent_type,
            "owner": owner,
            "scope": scope or [],
            "purpose": purpose,
        }
        if valid_from:
            payload["valid_from"] = valid_from
        if valid_until:
            payload["valid_until"] = valid_until
        if metadata:
            payload["metadata"] = metadata
        resp = self._http.post("/v1/identity/register", json=payload)
        resp.raise_for_status()
        return resp.json()

    def act(
        self,
        agent_id: str,
        action: str,
        action_scope: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"action": action}
        if action_scope:
            payload["action_scope"] = action_scope
        if data:
            payload["data"] = data
        resp = self._http.post(f"/v1/identity/{agent_id}/act", json=payload)
        resp.raise_for_status()
        return resp.json()

    def verify_identity(self, agent_id: str) -> dict[str, Any]:
        resp = self._http.get(f"/v1/identity/{agent_id}/verify")
        resp.raise_for_status()
        return resp.json()

    def get_identity_receipt(self, agent_id: str) -> str:
        resp = self._http.get(f"/v1/identity/{agent_id}/receipt")
        resp.raise_for_status()
        return resp.text

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> PruvClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
