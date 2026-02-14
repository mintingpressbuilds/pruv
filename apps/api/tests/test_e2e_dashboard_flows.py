"""End-to-end dashboard user flow tests.

Simulates every user flow the dashboard performs by calling the same API
endpoints the Next.js frontend uses (via lib/api.ts). Each test method
maps to a real user action in the dashboard UI.

Flow tested:
  1. Sign in (create JWT)
  2. Create an API key (Settings > API Keys)
  3. Create a chain via the API
  4. Verify the chain appears in the dashboard chain list (/chains)
  5. Open the chain timeline (/chains/[id]) — get chain + entries
  6. Expand an entry and verify X→Y state diff data is present
  7. Click verify — run verification and confirm result
  8. Create a checkpoint
  9. Click restore preview — confirm diff displays
  10. Navigate to /receipts — confirm the receipt appears
  11. Open the receipt — confirm PDF export link works
  12. Generate a share link — confirm /shared/[id] loads publicly
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_jwt_token, generate_api_key
from app.services.auth_service import auth_service

client = TestClient(app, raise_server_exceptions=False)


# ── Simulate sign-in: OAuth creates user, then we get a JWT ──────────────


@pytest.fixture(scope="module")
def user_token():
    """Simulate the full OAuth flow: register user, then get JWT.

    In the real dashboard, the user clicks "Continue with GitHub", the
    OAuth callback creates/gets the user, then returns a JWT. We replicate
    that by calling auth_service.get_or_create_oauth_user() first.
    """
    user = auth_service.get_or_create_oauth_user(
        provider="github",
        provider_id="gh_e2e_test",
        email="e2e@test.pruv.dev",
        name="E2E Test User",
    )
    return create_jwt_token(user["id"], scopes=["read", "write"])


@pytest.fixture(scope="module")
def auth(user_token):
    """Authorization header the dashboard sends on every request."""
    return {"Authorization": f"Bearer {user_token}"}


# ── 1. Sign in: verify /auth/me returns user info ────────────────────────


class TestSignIn:
    def test_auth_me_returns_user_info(self, auth):
        r = client.get("/v1/auth/me", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert data["id"]  # Has a user ID (from OAuth-created user)
        assert "read" in data["scopes"]
        assert "write" in data["scopes"]
        assert data["plan"] == "free"


# ── 2. Create an API key (Settings > API Keys page) ─────────────────────


class TestCreateApiKey:
    def test_create_api_key(self, auth):
        r = client.post("/v1/auth/api-keys",
                        json={"name": "e2e-test-key", "scopes": ["read", "write"]},
                        headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "e2e-test-key"
        assert "key" in data  # Full key shown once
        assert data["key"].startswith("pv_")
        assert "read" in data["scopes"]
        assert "write" in data["scopes"]

    def test_list_api_keys_shows_created_key(self, auth):
        r = client.get("/v1/auth/api-keys", headers=auth)
        assert r.status_code == 200
        keys = r.json()["keys"]
        assert any(k["name"] == "e2e-test-key" for k in keys)


# ── 3. Create a chain via the API ────────────────────────────────────────


@pytest.fixture(scope="module")
def chain_id(auth):
    """Create a chain and return its ID."""
    r = client.post("/v1/chains",
                    json={"name": "E2E Dashboard Chain",
                          "description": "Created during E2E test",
                          "tags": ["e2e", "dashboard"]},
                    headers=auth)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def populated_chain(auth, chain_id):
    """Add entries to the chain so we have data to display."""
    entries = [
        {"operation": "initialize", "y_state": {"version": 1, "status": "created"}},
        {"operation": "configure", "y_state": {"version": 2, "config": {"debug": True}}},
        {"operation": "deploy", "y_state": {"version": 3, "deployed": True}},
    ]
    for entry in entries:
        r = client.post(f"/v1/chains/{chain_id}/entries",
                        json=entry, headers=auth)
        assert r.status_code == 200
    return chain_id


# ── 4. Verify chain appears in chain list (/chains page) ────────────────


class TestChainList:
    def test_chain_appears_in_list(self, auth, populated_chain):
        r = client.get("/v1/chains", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        chain_ids = [c["id"] for c in data["chains"]]
        assert populated_chain in chain_ids

    def test_chain_has_correct_metadata(self, auth, populated_chain):
        r = client.get("/v1/chains", headers=auth)
        chains = r.json()["chains"]
        chain = next(c for c in chains if c["id"] == populated_chain)
        assert chain["name"] == "E2E Dashboard Chain"
        assert chain["length"] == 3
        assert "e2e" in chain["tags"]


# ── 5. Open chain timeline (/chains/[id] page) ──────────────────────────


class TestChainTimeline:
    def test_get_chain_detail(self, auth, populated_chain):
        """Dashboard fetches chain metadata for the header."""
        r = client.get(f"/v1/chains/{populated_chain}", headers=auth)
        assert r.status_code == 200
        chain = r.json()
        assert chain["name"] == "E2E Dashboard Chain"
        assert chain["length"] == 3
        assert chain["root_xy"] is not None
        assert chain["head_xy"] is not None

    def test_list_entries_for_timeline(self, auth, populated_chain):
        """Dashboard fetches entries to render the vertical timeline."""
        r = client.get(f"/v1/chains/{populated_chain}/entries", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        entries = data["entries"]
        assert entries[0]["operation"] == "initialize"
        assert entries[1]["operation"] == "configure"
        assert entries[2]["operation"] == "deploy"


# ── 6. Expand entry, verify X→Y diff renders ────────────────────────────


class TestEntryDetail:
    def test_entry_has_state_diff_data(self, auth, populated_chain):
        """When user clicks an entry node, the detail panel shows X→Y diff.
        The entry must have x, y, x_state, y_state for the StateDiff component."""
        r = client.get(f"/v1/chains/{populated_chain}/entries/0", headers=auth)
        assert r.status_code == 200
        entry = r.json()
        # First entry: x = GENESIS
        assert entry["x"] == "GENESIS"
        assert entry["y"] is not None
        assert entry["xy"].startswith("xy_")
        # y_state present for diff rendering
        assert entry["y_state"] is not None

    def test_chain_linking(self, auth, populated_chain):
        """Entry[1].x == Entry[0].y — the chain rule for diff continuity."""
        e0 = client.get(f"/v1/chains/{populated_chain}/entries/0", headers=auth).json()
        e1 = client.get(f"/v1/chains/{populated_chain}/entries/1", headers=auth).json()
        e2 = client.get(f"/v1/chains/{populated_chain}/entries/2", headers=auth).json()
        assert e1["x"] == e0["y"]
        assert e2["x"] == e1["y"]

    def test_validate_entry(self, auth, populated_chain):
        """Dashboard can validate individual entries."""
        r = client.get(f"/v1/chains/{populated_chain}/entries/1/validate", headers=auth)
        assert r.status_code == 200
        v = r.json()
        assert v["valid"] is True
        assert v["x_matches_prev_y"] is True
        assert v["proof_valid"] is True


# ── 7. Click verify — verification animation ────────────────────────────


class TestVerification:
    def test_verify_chain(self, auth, populated_chain):
        """User clicks the Verify badge button. Dashboard calls /verify."""
        r = client.get(f"/v1/chains/{populated_chain}/verify", headers=auth)
        assert r.status_code == 200
        result = r.json()
        assert result["valid"] is True
        assert result["length"] == 3
        assert result["break_index"] is None

    def test_certificate(self, auth, populated_chain):
        """Dashboard can also fetch a verification certificate."""
        r = client.get(f"/v1/certificate/{populated_chain}", headers=auth)
        assert r.status_code == 200
        cert = r.json()
        assert cert["valid"] is True
        assert cert["chain_name"] == "E2E Dashboard Chain"


# ── 8. Create a checkpoint ───────────────────────────────────────────────


@pytest.fixture(scope="module")
def checkpoint_id(auth, populated_chain):
    """Create a checkpoint from the checkpoint panel."""
    r = client.post(f"/v1/chains/{populated_chain}/checkpoints",
                    json={"name": "pre-deploy"},
                    headers=auth)
    assert r.status_code == 200
    return r.json()["id"]


class TestCheckpoints:
    def test_checkpoint_created(self, auth, populated_chain, checkpoint_id):
        r = client.get(f"/v1/chains/{populated_chain}/checkpoints", headers=auth)
        assert r.status_code == 200
        cps = r.json()["checkpoints"]
        assert any(cp["id"] == checkpoint_id for cp in cps)
        cp = next(cp for cp in cps if cp["id"] == checkpoint_id)
        assert cp["name"] == "pre-deploy"


# ── 9. Click restore preview, confirm diff displays ─────────────────────


class TestCheckpointPreview:
    def test_preview_restore(self, auth, populated_chain, checkpoint_id):
        """User clicks a checkpoint's restore button, sees preview diff."""
        r = client.get(
            f"/v1/chains/{populated_chain}/checkpoints/{checkpoint_id}/preview",
            headers=auth,
        )
        assert r.status_code == 200
        preview = r.json()
        assert preview["checkpoint_id"] == checkpoint_id
        assert preview["checkpoint_name"] == "pre-deploy"
        assert "entries_to_rollback" in preview
        assert "current_entry_index" in preview
        assert "target_entry_index" in preview


# ── 10. Navigate to /receipts, confirm receipt appears ───────────────────


@pytest.fixture(scope="module")
def receipt_id(auth, populated_chain):
    """Create a receipt (as dashboard does after verification)."""
    r = client.post("/v1/receipts",
                    json={"chain_id": populated_chain, "task": "e2e verification"},
                    headers=auth)
    assert r.status_code == 200
    return r.json()["id"]


class TestReceipts:
    def test_receipt_in_list(self, auth, receipt_id):
        """Receipts page lists all receipts."""
        r = client.get("/v1/receipts", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        ids = [rcpt["id"] for rcpt in data["receipts"]]
        assert receipt_id in ids

    def test_receipt_detail(self, auth, receipt_id):
        """Open a receipt — shows verification results."""
        r = client.get(f"/v1/receipts/{receipt_id}", headers=auth)
        assert r.status_code == 200
        rcpt = r.json()
        assert rcpt["id"] == receipt_id
        assert rcpt["all_verified"] is True
        assert rcpt["receipt_hash"] is not None


# ── 11. Open receipt, confirm PDF export link works ──────────────────────


class TestReceiptExport:
    def test_pdf_export(self, auth, receipt_id):
        """Dashboard calls /receipts/{id}/pdf for PDF export."""
        r = client.get(f"/v1/receipts/{receipt_id}/pdf", headers=auth)
        assert r.status_code == 200
        # Should return PDF-like data (at minimum, a valid response)
        assert r.headers.get("content-type") in (
            "application/pdf",
            "application/json",  # mock might return JSON
        )

    def test_badge_public(self, receipt_id):
        """Badge endpoint is public (no auth header)."""
        r = client.get(f"/v1/receipts/{receipt_id}/badge")
        assert r.status_code == 200
        assert "svg" in r.headers.get("content-type", "")


# ── 12. Generate share link, confirm public access ──────────────────────


class TestShareLink:
    def test_generate_share_link(self, auth, populated_chain):
        """User clicks Share on the chain detail page."""
        r = client.get(f"/v1/chains/{populated_chain}/share", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert "share_id" in data
        assert "share_url" in data

    def test_shared_chain_loads_publicly(self, auth, populated_chain):
        """The shared link loads the chain without authentication."""
        # First get the share_id
        share_resp = client.get(f"/v1/chains/{populated_chain}/share", headers=auth)
        share_id = share_resp.json()["share_id"]

        # Access without auth — this is the /shared/[id] page
        r = client.get(f"/v1/shared/{share_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["verified"] is True
        assert data["chain"]["name"] == "E2E Dashboard Chain"
        assert len(data["entries"]) == 3
        # Entries are ordered and have the expected operations
        assert data["entries"][0]["operation"] == "initialize"
        assert data["entries"][2]["operation"] == "deploy"


# ── Dashboard stats endpoint (overview page) ─────────────────────────────


class TestDashboardOverview:
    def test_dashboard_stats(self, auth, populated_chain, receipt_id):
        """Overview page fetches /v1/dashboard/stats."""
        r = client.get("/v1/dashboard/stats", headers=auth)
        assert r.status_code == 200
        stats = r.json()
        assert stats["total_chains"] >= 1
        assert stats["total_entries"] >= 3
        assert stats["total_receipts"] >= 1
        assert 0 <= stats["verified_percentage"] <= 100
        assert isinstance(stats["recent_activity"], list)


# ── Full flow: end-to-end in a single test ───────────────────────────────


class TestFullUserFlow:
    """Simulates the complete user journey through the dashboard."""

    def test_complete_flow(self):
        # 1. Sign in — OAuth creates user first, then JWT is issued
        user = auth_service.get_or_create_oauth_user(
            provider="github",
            provider_id="gh_flow_test",
            email="flow@test.pruv.dev",
            name="Flow Test User",
        )
        token = create_jwt_token(user["id"], scopes=["read", "write"])
        h = {"Authorization": f"Bearer {token}"}

        # 2. Create API key
        r = client.post("/v1/auth/api-keys", json={"name": "flow-key"}, headers=h)
        assert r.status_code == 200
        assert r.json()["key"].startswith("pv_")

        # 3. Create chain
        r = client.post("/v1/chains",
                        json={"name": "Full Flow Chain", "tags": ["flow"]}, headers=h)
        assert r.status_code == 200
        cid = r.json()["id"]

        # 4. Add entries
        for op in ["setup", "process", "finalize"]:
            r = client.post(f"/v1/chains/{cid}/entries",
                            json={"operation": op, "y_state": {"step": op}}, headers=h)
            assert r.status_code == 200

        # 5. Chain appears in list
        r = client.get("/v1/chains", headers=h)
        assert cid in [c["id"] for c in r.json()["chains"]]

        # 6. Open chain detail
        r = client.get(f"/v1/chains/{cid}", headers=h)
        assert r.json()["length"] == 3

        # 7. Load entries for timeline
        r = client.get(f"/v1/chains/{cid}/entries", headers=h)
        entries = r.json()["entries"]
        assert len(entries) == 3

        # 8. Expand entry — X→Y diff
        assert entries[0]["x"] == "GENESIS"
        assert entries[1]["x"] == entries[0]["y"]  # chain rule

        # 9. Verify chain
        r = client.get(f"/v1/chains/{cid}/verify", headers=h)
        assert r.json()["valid"] is True

        # 10. Create checkpoint
        r = client.post(f"/v1/chains/{cid}/checkpoints",
                        json={"name": "pre-ship"}, headers=h)
        assert r.status_code == 200
        cpid = r.json()["id"]

        # 11. Preview restore
        r = client.get(f"/v1/chains/{cid}/checkpoints/{cpid}/preview", headers=h)
        assert r.status_code == 200
        assert r.json()["checkpoint_name"] == "pre-ship"

        # 12. Create receipt
        r = client.post("/v1/receipts",
                        json={"chain_id": cid, "task": "flow-verify"}, headers=h)
        assert r.status_code == 200
        rid = r.json()["id"]

        # 13. Receipt in list
        r = client.get("/v1/receipts", headers=h)
        assert rid in [rcpt["id"] for rcpt in r.json()["receipts"]]

        # 14. Receipt detail + PDF
        r = client.get(f"/v1/receipts/{rid}", headers=h)
        assert r.json()["all_verified"] is True
        r = client.get(f"/v1/receipts/{rid}/pdf", headers=h)
        assert r.status_code == 200

        # 15. Share chain
        r = client.get(f"/v1/chains/{cid}/share", headers=h)
        share_id = r.json()["share_id"]

        # 16. Public shared view — no auth
        r = client.get(f"/v1/shared/{share_id}")
        assert r.status_code == 200
        assert r.json()["verified"] is True
        assert len(r.json()["entries"]) == 3

        # 17. Dashboard stats
        r = client.get("/v1/dashboard/stats", headers=h)
        assert r.status_code == 200
        assert r.json()["total_chains"] >= 1
