"""Tests for the pruv API backend."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import generate_api_key, hash_api_key

client = TestClient(app)

# Test API key
TEST_KEY = generate_api_key("pv_test_")
AUTH_HEADER = {"Authorization": f"Bearer {TEST_KEY}"}


class TestHealth:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200


class TestChains:
    def test_create_chain(self):
        resp = client.post(
            "/v1/chains",
            json={"name": "test-chain"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test-chain"
        assert "id" in data

    def test_list_chains(self):
        # Create a chain first
        client.post("/v1/chains", json={"name": "list-test"}, headers=AUTH_HEADER)
        resp = client.get("/v1/chains", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_get_chain(self):
        create_resp = client.post(
            "/v1/chains", json={"name": "get-test"}, headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        resp = client.get(f"/v1/chains/{chain_id}", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["name"] == "get-test"

    def test_get_nonexistent_chain(self):
        resp = client.get("/v1/chains/nonexistent", headers=AUTH_HEADER)
        assert resp.status_code == 404


class TestEntries:
    def _create_chain(self) -> str:
        resp = client.post(
            "/v1/chains", json={"name": "entry-test"}, headers=AUTH_HEADER,
        )
        return resp.json()["id"]

    def test_append_entry(self):
        chain_id = self._create_chain()
        resp = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "deploy", "y_state": {"version": "1.0"}},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["operation"] == "deploy"
        assert data["index"] == 0
        assert data["x"] == "GENESIS"
        assert data["xy"].startswith("xy_")

    def test_chain_linking(self):
        chain_id = self._create_chain()
        r1 = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "step1", "y_state": {"v": 1}},
            headers=AUTH_HEADER,
        ).json()
        r2 = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "step2", "y_state": {"v": 2}},
            headers=AUTH_HEADER,
        ).json()
        assert r2["x"] == r1["y"]

    def test_batch_append(self):
        chain_id = self._create_chain()
        resp = client.post(
            f"/v1/chains/{chain_id}/entries/batch",
            json={"entries": [
                {"operation": "a", "y_state": {"v": 1}},
                {"operation": "b", "y_state": {"v": 2}},
                {"operation": "c", "y_state": {"v": 3}},
            ]},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_list_entries(self):
        chain_id = self._create_chain()
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op1", "y_state": {"v": 1}},
            headers=AUTH_HEADER,
        )
        resp = client.get(f"/v1/chains/{chain_id}/entries", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


class TestVerification:
    def test_verify_chain(self):
        # Create chain with entries
        create_resp = client.post(
            "/v1/chains", json={"name": "verify-test"}, headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op1", "y_state": {"v": 1}},
            headers=AUTH_HEADER,
        )
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op2", "y_state": {"v": 2}},
            headers=AUTH_HEADER,
        )

        resp = client.get(f"/v1/chains/{chain_id}/verify", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["length"] == 2

    def test_verify_empty_chain(self):
        create_resp = client.post(
            "/v1/chains", json={"name": "empty-verify"}, headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        resp = client.get(f"/v1/chains/{chain_id}/verify", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["valid"] is True


class TestSharing:
    def test_share_chain(self):
        create_resp = client.post(
            "/v1/chains", json={"name": "share-test"}, headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        resp = client.get(f"/v1/chains/{chain_id}/share", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert "share_id" in data
        assert "share_url" in data

    def test_view_shared_chain(self):
        create_resp = client.post(
            "/v1/chains", json={"name": "public-test"}, headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op1", "y_state": {"v": 1}},
            headers=AUTH_HEADER,
        )
        share_resp = client.get(f"/v1/chains/{chain_id}/share", headers=AUTH_HEADER)
        share_id = share_resp.json()["share_id"]

        resp = client.get(f"/v1/shared/{share_id}")
        assert resp.status_code == 200


class TestCheckpoints:
    def _create_chain_with_entries(self) -> str:
        create_resp = client.post(
            "/v1/chains", json={"name": "cp-test"}, headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op1", "y_state": {"v": 1}},
            headers=AUTH_HEADER,
        )
        return chain_id

    def test_create_checkpoint(self):
        chain_id = self._create_chain_with_entries()
        resp = client.post(
            f"/v1/chains/{chain_id}/checkpoints",
            json={"name": "before-change"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "before-change"

    def test_list_checkpoints(self):
        chain_id = self._create_chain_with_entries()
        client.post(
            f"/v1/chains/{chain_id}/checkpoints",
            json={"name": "cp1"},
            headers=AUTH_HEADER,
        )
        resp = client.get(
            f"/v1/chains/{chain_id}/checkpoints",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        assert len(resp.json()["checkpoints"]) >= 1


class TestCertificate:
    def test_get_certificate(self):
        create_resp = client.post(
            "/v1/chains", json={"name": "cert-test"}, headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op1", "y_state": {"v": 1}},
            headers=AUTH_HEADER,
        )
        resp = client.get(f"/v1/certificate/{chain_id}", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["chain_name"] == "cert-test"


class TestAuth:
    def test_missing_auth(self):
        resp = client.get("/v1/chains")
        assert resp.status_code == 401

    def test_invalid_token(self):
        resp = client.get(
            "/v1/chains",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert resp.status_code == 401


class TestAutoRedact:
    def test_redacts_secrets_in_entries(self):
        create_resp = client.post(
            "/v1/chains", json={"name": "redact-test", "auto_redact": True},
            headers=AUTH_HEADER,
        )
        chain_id = create_resp.json()["id"]
        resp = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={
                "operation": "config",
                "y_state": {"password": "secret123", "api_key": "sk_live_abc123"},
            },
            headers=AUTH_HEADER,
        )
        data = resp.json()
        assert data["y_state"]["password"] == "[REDACTED]"
        assert data["y_state"]["api_key"] == "[REDACTED]"
