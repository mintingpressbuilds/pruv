"""Tests for the anomaly detection alert service and API endpoint."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import generate_api_key
from app.services.alerts import (
    AlertSeverity,
    analyze_chain,
)

client = TestClient(app)

TEST_KEY = generate_api_key("pv_test_")
AUTH_HEADER = {"Authorization": f"Bearer {TEST_KEY}"}


def _make_chain(chain_id: str = "test-chain-1") -> dict:
    return {"id": chain_id, "name": "test", "length": 0}


def _make_entry(
    index: int,
    operation: str,
    metadata: dict | None = None,
    y_state: dict | None = None,
    ts_offset: float = 0.0,
) -> dict:
    return {
        "id": f"entry-{index}",
        "chain_id": "test-chain-1",
        "index": index,
        "timestamp": time.time() + ts_offset,
        "operation": operation,
        "x": "GENESIS" if index == 0 else f"hash-{index - 1}",
        "y": f"hash-{index}",
        "xy": f"xy_proof-{index}",
        "status": "success",
        "metadata": metadata or {},
        "y_state": y_state or {},
    }


# ─── Unit tests for analyze_chain ────────────────────────────────────────────


class TestHighErrorRate:
    def test_no_alert_below_threshold(self):
        """<= 30% error rate should not trigger."""
        chain = _make_chain()
        entries = [_make_entry(i, "task.complete") for i in range(8)]
        entries.append(_make_entry(8, "task.error"))
        entries.append(_make_entry(9, "task.complete"))
        # 1/10 = 10%
        alerts = analyze_chain(chain, entries)
        error_alerts = [a for a in alerts if a.rule == "high_error_rate"]
        assert len(error_alerts) == 0

    def test_alert_above_threshold(self):
        """High error rate (>30%) should trigger warning."""
        chain = _make_chain()
        entries = []
        for i in range(10):
            op = "task.error" if i < 5 else "task.complete"
            entries.append(_make_entry(i, op))
        # 5/10 = 50%
        alerts = analyze_chain(chain, entries)
        error_alerts = [a for a in alerts if a.rule == "high_error_rate"]
        assert len(error_alerts) == 1
        assert error_alerts[0].severity == AlertSeverity.WARNING
        assert "50%" in error_alerts[0].message

    def test_no_alert_with_few_entries(self):
        """Chains with <= 5 entries should not trigger."""
        chain = _make_chain()
        entries = [_make_entry(i, "task.error") for i in range(5)]
        alerts = analyze_chain(chain, entries)
        error_alerts = [a for a in alerts if a.rule == "high_error_rate"]
        assert len(error_alerts) == 0


class TestHighActionRate:
    def test_no_alert_below_100_entries(self):
        """Chains with <= 100 entries should not trigger."""
        chain = _make_chain()
        entries = [_make_entry(i, "task.complete", ts_offset=i) for i in range(50)]
        alerts = analyze_chain(chain, entries)
        rate_alerts = [a for a in alerts if a.rule == "high_action_rate"]
        assert len(rate_alerts) == 0

    def test_alert_high_rate(self):
        """More than 30 actions/minute should trigger warning."""
        chain = _make_chain()
        base_ts = time.time()
        entries = []
        for i in range(120):
            e = _make_entry(i, "task.complete")
            # 120 entries in 60 seconds = 120/min
            e["timestamp"] = base_ts + i * 0.5
            entries.append(e)
        alerts = analyze_chain(chain, entries)
        rate_alerts = [a for a in alerts if a.rule == "high_action_rate"]
        assert len(rate_alerts) == 1
        assert rate_alerts[0].severity == AlertSeverity.WARNING


class TestNewTools:
    def test_no_alert_for_first_tools(self):
        """First 3 tools should not trigger alerts."""
        chain = _make_chain()
        entries = [
            _make_entry(0, "tool.start", metadata={"tool": "search"}),
            _make_entry(1, "tool.start", metadata={"tool": "email"}),
            _make_entry(2, "tool.start", metadata={"tool": "calendar"}),
        ]
        alerts = analyze_chain(chain, entries)
        tool_alerts = [a for a in alerts if a.rule == "new_tool"]
        assert len(tool_alerts) == 0

    def test_alert_for_new_tool_after_baseline(self):
        """A new tool after 3+ established tools should trigger info."""
        chain = _make_chain()
        entries = [
            _make_entry(0, "tool.start", metadata={"tool": "search"}),
            _make_entry(1, "tool.start", metadata={"tool": "email"}),
            _make_entry(2, "tool.start", metadata={"tool": "calendar"}),
            _make_entry(3, "tool.start", metadata={"tool": "browser"}),
            _make_entry(4, "tool.start", metadata={"tool": "shell_exec"}),
        ]
        alerts = analyze_chain(chain, entries)
        tool_alerts = [a for a in alerts if a.rule == "new_tool"]
        assert len(tool_alerts) >= 1
        assert tool_alerts[0].severity == AlertSeverity.INFO
        assert "shell_exec" in tool_alerts[0].message


class TestSensitiveFileAccess:
    def test_alert_on_env_file(self):
        """Accessing .env should trigger critical alert."""
        chain = _make_chain()
        entries = [
            _make_entry(0, "file.access", metadata={"path": "/app/.env"}),
        ]
        alerts = analyze_chain(chain, entries)
        file_alerts = [a for a in alerts if a.rule == "sensitive_file_access"]
        assert len(file_alerts) == 1
        assert file_alerts[0].severity == AlertSeverity.CRITICAL

    def test_alert_on_ssh_directory(self):
        """Accessing .ssh should trigger critical alert."""
        chain = _make_chain()
        entries = [
            _make_entry(0, "file.access", metadata={"path": "/home/user/.ssh/id_rsa"}),
        ]
        alerts = analyze_chain(chain, entries)
        file_alerts = [a for a in alerts if a.rule == "sensitive_file_access"]
        assert len(file_alerts) == 1
        assert ".ssh" in file_alerts[0].message

    def test_no_alert_on_normal_file(self):
        """Normal file access should not trigger alert."""
        chain = _make_chain()
        entries = [
            _make_entry(0, "file.access", metadata={"path": "/app/src/main.py"}),
        ]
        alerts = analyze_chain(chain, entries)
        file_alerts = [a for a in alerts if a.rule == "sensitive_file_access"]
        assert len(file_alerts) == 0


class TestNewDomains:
    def test_no_alert_for_first_domains(self):
        """First 2 domains should not trigger alerts."""
        chain = _make_chain()
        entries = [
            _make_entry(0, "api.call", metadata={"url": "https://api.openai.com/v1/chat"}),
            _make_entry(1, "api.call", metadata={"url": "https://api.stripe.com/v1/charges"}),
        ]
        alerts = analyze_chain(chain, entries)
        domain_alerts = [a for a in alerts if a.rule == "new_api_domain"]
        assert len(domain_alerts) == 0

    def test_alert_for_new_domain_after_baseline(self):
        """A new domain after 2+ established should trigger info."""
        chain = _make_chain()
        entries = [
            _make_entry(0, "api.call", metadata={"url": "https://api.openai.com/v1/chat"}),
            _make_entry(1, "api.call", metadata={"url": "https://api.stripe.com/v1/charges"}),
            _make_entry(2, "api.call", metadata={"url": "https://api.github.com/repos"}),
            _make_entry(3, "api.call", metadata={"url": "https://evil.example.com/exfil"}),
        ]
        alerts = analyze_chain(chain, entries)
        domain_alerts = [a for a in alerts if a.rule == "new_api_domain"]
        assert len(domain_alerts) >= 1
        assert domain_alerts[0].severity == AlertSeverity.INFO


class TestEmptyChain:
    def test_no_alerts_on_empty(self):
        """Empty chain should return no alerts."""
        chain = _make_chain()
        alerts = analyze_chain(chain, [])
        assert alerts == []


# ─── Integration tests via API ────────────────────────────────────────────────


class TestAlertsEndpoint:
    def _create_chain(self) -> str:
        resp = client.post(
            "/v1/chains",
            json={"name": "alert-test-chain"},
            headers=AUTH_HEADER,
        )
        return resp.json()["id"]

    def test_alerts_endpoint_empty_chain(self):
        """GET /v1/chains/{id}/alerts on empty chain returns no alerts."""
        chain_id = self._create_chain()
        resp = client.get(f"/v1/chains/{chain_id}/alerts", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["chain_id"] == chain_id
        assert data["alerts"] == []
        assert "analyzed_at" in data

    def test_alerts_endpoint_with_errors(self):
        """GET /v1/chains/{id}/alerts detects high error rate."""
        chain_id = self._create_chain()

        # Add 10 entries, 5 of which are errors
        for i in range(10):
            op = "task.error" if i < 5 else "task.complete"
            client.post(
                f"/v1/chains/{chain_id}/entries",
                json={"operation": op, "y_state": {"seq": i}},
                headers=AUTH_HEADER,
            )

        resp = client.get(f"/v1/chains/{chain_id}/alerts", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        rules = [a["rule"] for a in data["alerts"]]
        assert "high_error_rate" in rules

    def test_alerts_endpoint_sensitive_file(self):
        """GET /v1/chains/{id}/alerts detects sensitive file access."""
        chain_id = self._create_chain()
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={
                "operation": "file.access",
                "y_state": {"path": "/etc/shadow"},
                "metadata": {"path": "/etc/shadow"},
            },
            headers=AUTH_HEADER,
        )
        resp = client.get(f"/v1/chains/{chain_id}/alerts", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        rules = [a["rule"] for a in data["alerts"]]
        assert "sensitive_file_access" in rules
        severity = next(a["severity"] for a in data["alerts"] if a["rule"] == "sensitive_file_access")
        assert severity == "critical"

    def test_alerts_endpoint_nonexistent_chain(self):
        """GET /v1/chains/{id}/alerts on nonexistent chain returns 404."""
        resp = client.get("/v1/chains/nonexistent/alerts", headers=AUTH_HEADER)
        assert resp.status_code == 404


class TestExportEndpoint:
    def _create_chain_with_entries(self) -> str:
        resp = client.post(
            "/v1/chains",
            json={"name": "export-test"},
            headers=AUTH_HEADER,
        )
        chain_id = resp.json()["id"]
        for i in range(3):
            client.post(
                f"/v1/chains/{chain_id}/entries",
                json={"operation": f"step-{i}", "y_state": {"v": i}},
                headers=AUTH_HEADER,
            )
        return chain_id

    def test_export_returns_html(self):
        """GET /v1/chains/{id}/export returns valid HTML."""
        chain_id = self._create_chain_with_entries()
        resp = client.get(f"/v1/chains/{chain_id}/export", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        body = resp.text
        assert "<!DOCTYPE html>" in body
        assert "export-test" in body
        assert "pruv chain" in body

    def test_export_contains_entries(self):
        """Exported HTML contains entry data."""
        chain_id = self._create_chain_with_entries()
        resp = client.get(f"/v1/chains/{chain_id}/export", headers=AUTH_HEADER)
        body = resp.text
        assert "step-0" in body
        assert "step-1" in body
        assert "step-2" in body

    def test_export_has_verify_script(self):
        """Exported HTML contains self-verification JavaScript."""
        chain_id = self._create_chain_with_entries()
        resp = client.get(f"/v1/chains/{chain_id}/export", headers=AUTH_HEADER)
        body = resp.text
        assert "verifyChain" in body
        assert "crypto.subtle.digest" in body

    def test_export_nonexistent_chain(self):
        """GET /v1/chains/{id}/export on nonexistent chain returns 404."""
        resp = client.get("/v1/chains/nonexistent/export", headers=AUTH_HEADER)
        assert resp.status_code == 404
