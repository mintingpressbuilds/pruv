"""Test write scope enforcement.

Every POST, PATCH, DELETE route on chains, entries, checkpoints, receipts,
webhooks, and auth must require the 'write' scope.

A read-only JWT (scopes=["read"]) must get 403 on every write route.
A read-write JWT must get 200 (or 404 for missing resources) on every write route.
A read-only JWT must get 200 on every read route.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_jwt_token, generate_api_key

client = TestClient(app, raise_server_exceptions=False)

# Read-only JWT — only ["read"] scope
READ_ONLY_TOKEN = create_jwt_token("readonly_user", scopes=["read"])
READ_ONLY = {"Authorization": f"Bearer {READ_ONLY_TOKEN}"}

# Read-write JWT — ["read", "write"] scopes
RW_TOKEN = create_jwt_token("rw_user", scopes=["read", "write"])
RW_AUTH = {"Authorization": f"Bearer {RW_TOKEN}"}

# Full-privilege API key (read+write by default)
API_KEY = generate_api_key("pv_test_")
KEY_AUTH = {"Authorization": f"Bearer {API_KEY}"}


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def chain_id():
    """Create a chain for tests to reference."""
    r = client.post("/v1/chains", json={"name": "scope-test"}, headers=RW_AUTH)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def entry_chain_id():
    """Chain with an entry for entry-related tests."""
    r = client.post("/v1/chains", json={"name": "entry-scope-test"}, headers=KEY_AUTH)
    cid = r.json()["id"]
    client.post(f"/v1/chains/{cid}/entries",
                json={"operation": "init", "y_state": {"v": 1}}, headers=KEY_AUTH)
    return cid


@pytest.fixture(scope="module")
def checkpoint_id(entry_chain_id):
    """Create a checkpoint for tests."""
    r = client.post(f"/v1/chains/{entry_chain_id}/checkpoints",
                    json={"name": "scope-cp"}, headers=KEY_AUTH)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def receipt_id(entry_chain_id):
    """Create a receipt for tests."""
    r = client.post("/v1/receipts",
                    json={"chain_id": entry_chain_id, "task": "scope-test"}, headers=KEY_AUTH)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def webhook_id():
    """Create a webhook for tests."""
    r = client.post("/v1/webhooks",
                    json={"url": "https://example.com/hook", "events": ["chain.created"]},
                    headers=KEY_AUTH)
    assert r.status_code == 200
    return r.json()["id"]


# ── Write routes must reject read-only JWT with 403 ──────────


class TestWriteRoutesRejectReadOnly:
    """Every write route must return 403 for a read-only JWT."""

    def test_create_chain(self):
        r = client.post("/v1/chains", json={"name": "rejected"}, headers=READ_ONLY)
        assert r.status_code == 403

    def test_update_chain(self, chain_id):
        r = client.patch(f"/v1/chains/{chain_id}", json={"name": "nope"}, headers=READ_ONLY)
        assert r.status_code == 403

    def test_delete_chain(self, chain_id):
        r = client.delete(f"/v1/chains/{chain_id}", headers=READ_ONLY)
        assert r.status_code == 403

    def test_undo_entry(self, entry_chain_id):
        r = client.post(f"/v1/chains/{entry_chain_id}/undo", headers=READ_ONLY)
        assert r.status_code == 403

    def test_append_entry(self, entry_chain_id):
        r = client.post(f"/v1/chains/{entry_chain_id}/entries",
                        json={"operation": "nope", "y_state": {"v": 2}}, headers=READ_ONLY)
        assert r.status_code == 403

    def test_batch_append_entries(self, entry_chain_id):
        r = client.post(f"/v1/chains/{entry_chain_id}/entries/batch",
                        json={"entries": [{"operation": "nope", "y_state": {"v": 3}}]},
                        headers=READ_ONLY)
        assert r.status_code == 403

    def test_create_checkpoint(self, entry_chain_id):
        r = client.post(f"/v1/chains/{entry_chain_id}/checkpoints",
                        json={"name": "nope"}, headers=READ_ONLY)
        assert r.status_code == 403

    def test_restore_checkpoint(self, entry_chain_id, checkpoint_id):
        r = client.post(
            f"/v1/chains/{entry_chain_id}/checkpoints/{checkpoint_id}/restore",
            headers=READ_ONLY,
        )
        assert r.status_code == 403

    def test_create_receipt(self, entry_chain_id):
        r = client.post("/v1/receipts",
                        json={"chain_id": entry_chain_id, "task": "nope"}, headers=READ_ONLY)
        assert r.status_code == 403

    def test_create_webhook(self):
        r = client.post("/v1/webhooks",
                        json={"url": "https://example.com/nope", "events": ["chain.created"]},
                        headers=READ_ONLY)
        assert r.status_code == 403

    def test_update_webhook(self, webhook_id):
        r = client.patch(f"/v1/webhooks/{webhook_id}",
                         json={"events": ["entry.appended"]}, headers=READ_ONLY)
        assert r.status_code == 403

    def test_delete_webhook(self, webhook_id):
        r = client.delete(f"/v1/webhooks/{webhook_id}", headers=READ_ONLY)
        assert r.status_code == 403

    def test_create_api_key(self):
        r = client.post("/v1/auth/api-keys",
                        json={"name": "nope"}, headers=READ_ONLY)
        assert r.status_code == 403

    def test_revoke_api_key(self):
        r = client.delete("/v1/auth/api-keys/fake_id", headers=READ_ONLY)
        assert r.status_code == 403


# ── Read routes must accept read-only JWT with 200 ───────────


class TestReadRoutesAcceptReadOnly:
    """Every read route must return 200 for a read-only JWT."""

    def test_list_chains(self):
        r = client.get("/v1/chains", headers=READ_ONLY)
        assert r.status_code == 200

    def test_get_chain(self, chain_id):
        # Read-only user won't own this chain, so 404 is expected (ownership check).
        # The point is it's NOT 403. Auth passes, ownership is a separate concern.
        r = client.get(f"/v1/chains/{chain_id}", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_verify_chain(self, chain_id):
        r = client.get(f"/v1/chains/{chain_id}/verify", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_share_chain(self, chain_id):
        r = client.get(f"/v1/chains/{chain_id}/share", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_list_entries(self, entry_chain_id):
        r = client.get(f"/v1/chains/{entry_chain_id}/entries", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_get_entry(self, entry_chain_id):
        r = client.get(f"/v1/chains/{entry_chain_id}/entries/0", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_validate_entry(self, entry_chain_id):
        r = client.get(f"/v1/chains/{entry_chain_id}/entries/0/validate", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_list_checkpoints(self, entry_chain_id):
        r = client.get(f"/v1/chains/{entry_chain_id}/checkpoints", headers=READ_ONLY)
        assert r.status_code == 200

    def test_preview_checkpoint(self, entry_chain_id, checkpoint_id):
        r = client.get(
            f"/v1/chains/{entry_chain_id}/checkpoints/{checkpoint_id}/preview",
            headers=READ_ONLY,
        )
        assert r.status_code in (200, 404)

    def test_list_receipts(self):
        r = client.get("/v1/receipts", headers=READ_ONLY)
        assert r.status_code == 200

    def test_get_receipt(self, receipt_id):
        r = client.get(f"/v1/receipts/{receipt_id}", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_get_receipt_pdf(self, receipt_id):
        r = client.get(f"/v1/receipts/{receipt_id}/pdf", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_list_webhooks(self):
        r = client.get("/v1/webhooks", headers=READ_ONLY)
        assert r.status_code == 200

    def test_get_webhook(self, webhook_id):
        r = client.get(f"/v1/webhooks/{webhook_id}", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_list_api_keys(self):
        r = client.get("/v1/auth/api-keys", headers=READ_ONLY)
        assert r.status_code == 200

    def test_get_me(self):
        r = client.get("/v1/auth/me", headers=READ_ONLY)
        assert r.status_code == 200

    def test_get_usage(self):
        r = client.get("/v1/auth/usage", headers=READ_ONLY)
        assert r.status_code == 200

    def test_dashboard_stats(self):
        r = client.get("/v1/dashboard/stats", headers=READ_ONLY)
        assert r.status_code == 200

    def test_certificate(self, chain_id):
        r = client.get(f"/v1/certificate/{chain_id}", headers=READ_ONLY)
        assert r.status_code in (200, 404)

    def test_analytics_usage(self):
        r = client.get("/analytics/usage", headers=READ_ONLY)
        assert r.status_code == 200


# ── Write routes must accept read-write JWT ───────────────────


class TestWriteRoutesAcceptReadWrite:
    """Write routes accept tokens with ['read', 'write'] scopes."""

    def test_create_chain(self):
        r = client.post("/v1/chains", json={"name": "rw-test"}, headers=RW_AUTH)
        assert r.status_code == 200

    def test_append_entry(self):
        # Create a fresh chain for this test
        cid = client.post("/v1/chains", json={"name": "rw-entry"}, headers=RW_AUTH).json()["id"]
        r = client.post(f"/v1/chains/{cid}/entries",
                        json={"operation": "test", "y_state": {"v": 1}}, headers=RW_AUTH)
        assert r.status_code == 200

    def test_create_receipt(self):
        cid = client.post("/v1/chains", json={"name": "rw-receipt"}, headers=RW_AUTH).json()["id"]
        r = client.post("/v1/receipts",
                        json={"chain_id": cid, "task": "rw-test"}, headers=RW_AUTH)
        assert r.status_code == 200

    def test_create_webhook(self):
        r = client.post("/v1/webhooks",
                        json={"url": "https://example.com/rw", "events": ["chain.created"]},
                        headers=RW_AUTH)
        assert r.status_code == 200

    def test_create_api_key(self):
        r = client.post("/v1/auth/api-keys",
                        json={"name": "rw-key"}, headers=RW_AUTH)
        assert r.status_code in (200, 400)

    def test_api_key_has_write(self):
        """API keys (pv_test_*) get read+write by default, so writes work."""
        r = client.post("/v1/chains", json={"name": "key-write"}, headers=KEY_AUTH)
        assert r.status_code == 200


# ── 403 error message is informative ──────────────────────────


class TestScopeErrorMessage:
    """403 responses include the missing scope name."""

    def test_missing_write_scope_message(self):
        r = client.post("/v1/chains", json={"name": "msg-test"}, headers=READ_ONLY)
        assert r.status_code == 403
        assert "write" in r.json()["detail"].lower()
