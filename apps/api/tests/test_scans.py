"""Tests for scan endpoints and HTML export verification."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import generate_api_key

client = TestClient(app)

TEST_KEY = generate_api_key("pv_test_")
AUTH_HEADER = {"Authorization": f"Bearer {TEST_KEY}"}


def _create_chain_with_entries():
    """Create a chain with entries and return chain_id."""
    resp = client.post(
        "/v1/chains",
        json={"name": "scan-test-chain"},
        headers=AUTH_HEADER,
    )
    chain_id = resp.json()["id"]

    client.post(
        f"/v1/chains/{chain_id}/entries",
        json={"operation": "init", "x_state": {"v": 1}, "y_state": {"v": 2}},
        headers=AUTH_HEADER,
    )
    client.post(
        f"/v1/chains/{chain_id}/entries",
        json={"operation": "update", "x_state": {"v": 2}, "y_state": {"v": 3}},
        headers=AUTH_HEADER,
    )
    return chain_id


class TestScanByChainId:
    def test_scan_valid_chain(self):
        chain_id = _create_chain_with_entries()
        resp = client.post(
            "/v1/scans",
            json={"chain_id": chain_id},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["chain_id"] == chain_id
        assert data["findings"] == []
        assert data["id"]
        assert data["started_at"]
        assert data["completed_at"]

    def test_scan_chain_not_found(self):
        resp = client.post(
            "/v1/scans",
            json={"chain_id": "nonexistent"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 404

    def test_scan_no_chain_id(self):
        resp = client.post(
            "/v1/scans",
            json={},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_scan_requires_auth(self):
        resp = client.post(
            "/v1/scans",
            json={"chain_id": "test"},
        )
        assert resp.status_code == 401

    def test_scan_with_options(self):
        chain_id = _create_chain_with_entries()
        resp = client.post(
            "/v1/scans",
            json={
                "chain_id": chain_id,
                "options": {
                    "deep_verify": True,
                    "check_signatures": False,
                    "generate_receipt": False,
                },
            },
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["findings"] == []


class TestScanByFileUpload:
    def test_upload_valid_file(self):
        # Build a valid chain JSON file
        from xycore.crypto import compute_xy, hash_state

        x0 = "GENESIS"
        y0 = hash_state({"v": 1})
        xy0 = compute_xy(x0, "init", y0, 1000.0)

        x1 = y0
        y1 = hash_state({"v": 2})
        xy1 = compute_xy(x1, "update", y1, 1001.0)

        file_data = {
            "chain_id": "file-test",
            "entries": [
                {"x": x0, "y": y0, "xy": xy0, "operation": "init", "timestamp": 1000.0},
                {"x": x1, "y": y1, "xy": xy1, "operation": "update", "timestamp": 1001.0},
            ],
        }

        resp = client.post(
            "/v1/scans",
            files={"file": ("chain.json", json.dumps(file_data).encode(), "application/json")},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["chain_id"] == "file-test"
        assert data["findings"] == []

    def test_upload_broken_chain(self):
        file_data = {
            "chain_id": "broken-test",
            "entries": [
                {"x": "GENESIS", "y": "hash1", "xy": "xy_wrong", "operation": "init", "timestamp": 1000.0},
                {"x": "wrong_link", "y": "hash2", "xy": "xy_wrong2", "operation": "update", "timestamp": 1001.0},
            ],
        }

        resp = client.post(
            "/v1/scans",
            files={"file": ("chain.json", json.dumps(file_data).encode(), "application/json")},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should find chain break and proof mismatch
        assert len(data["findings"]) > 0
        types = [f["type"] for f in data["findings"]]
        assert "chain_break" in types or "proof_mismatch" in types

    def test_upload_empty_entries(self):
        file_data = {"chain_id": "empty", "entries": []}
        resp = client.post(
            "/v1/scans",
            files={"file": ("chain.json", json.dumps(file_data).encode(), "application/json")},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert any(f["type"] == "empty_chain" for f in data["findings"])

    def test_upload_invalid_json(self):
        resp = client.post(
            "/v1/scans",
            files={"file": ("bad.json", b"not json{{{", "application/json")},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400


class TestScanStatus:
    def test_get_scan_result(self):
        chain_id = _create_chain_with_entries()
        resp = client.post(
            "/v1/scans",
            json={"chain_id": chain_id},
            headers=AUTH_HEADER,
        )
        scan_id = resp.json()["id"]

        resp2 = client.get(f"/v1/scans/{scan_id}", headers=AUTH_HEADER)
        assert resp2.status_code == 200
        assert resp2.json()["id"] == scan_id

    def test_scan_not_found(self):
        resp = client.get("/v1/scans/nonexistent", headers=AUTH_HEADER)
        assert resp.status_code == 404


class TestHTMLExportSeparator:
    """Verify the HTML export uses ':' separator matching xycore.compute_xy."""

    def test_export_uses_colon_separator(self):
        chain_id = _create_chain_with_entries()
        resp = client.get(
            f"/v1/chains/{chain_id}/export",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        html = resp.text
        # The JavaScript should use ':' not '|'
        assert "e.x + ':' + e.operation + ':' + e.y + ':' + String(e.timestamp)" in html
        assert "e.x + '|'" not in html
