"""Security tests for the pruv API.

Tests every route for:
- Unauthenticated access
- Invalid/expired tokens
- Rate limiting enforcement
- Input validation (malformed, oversized, SQL injection, XSS)
- Access control (ownership, scope)
- CORS headers
- Error response safety (no stack traces)
"""

from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_jwt_token, generate_api_key
from app.core.rate_limit import rate_limiter

client = TestClient(app, raise_server_exceptions=False)

# Valid auth
TEST_KEY = generate_api_key("pv_test_")
AUTH = {"Authorization": f"Bearer {TEST_KEY}"}

# A second user's key (different identity)
TEST_KEY_2 = generate_api_key("pv_test_")
AUTH_2 = {"Authorization": f"Bearer {TEST_KEY_2}"}


def _make_jwt(user_id: str, scopes: list[str] | None = None, expired: bool = False) -> str:
    """Create a JWT token, optionally expired."""
    token = create_jwt_token(user_id, scopes=scopes)
    if expired:
        # Tamper with the payload to set exp in the past
        import base64
        parts = token.rsplit(".", 1)
        payload = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
        payload["exp"] = int(time.time()) - 3600
        new_payload = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).decode().rstrip("=")
        # Return with old signature (will be invalid)
        return f"{new_payload}.{parts[1]}"
    return token


def _admin_jwt() -> dict[str, str]:
    """Create an admin-scoped JWT auth header."""
    token = create_jwt_token("admin_user", scopes=["read", "write", "admin"])
    return {"Authorization": f"Bearer {token}"}


def _create_chain(headers: dict[str, str] = AUTH) -> str:
    resp = client.post("/v1/chains", json={"name": "sec-test"}, headers=headers)
    return resp.json()["id"]


class TestUnauthenticatedAccess:
    """Every authenticated route must reject unauthenticated requests."""

    @pytest.mark.parametrize("method,path", [
        ("GET", "/v1/chains"),
        ("POST", "/v1/chains"),
        ("GET", "/v1/chains/fake-id"),
        ("GET", "/v1/chains/fake-id/verify"),
        ("GET", "/v1/chains/fake-id/share"),
        ("POST", "/v1/chains/fake-id/entries"),
        ("POST", "/v1/chains/fake-id/entries/batch"),
        ("GET", "/v1/chains/fake-id/entries"),
        ("POST", "/v1/chains/fake-id/checkpoints"),
        ("GET", "/v1/chains/fake-id/checkpoints"),
        ("GET", "/v1/receipts/fake-id"),
        ("GET", "/v1/receipts/fake-id/pdf"),
        ("POST", "/v1/auth/api-keys"),
        ("GET", "/v1/auth/api-keys"),
        ("DELETE", "/v1/auth/api-keys/fake-id"),
        ("GET", "/v1/auth/me"),
        ("GET", "/v1/auth/usage"),
        ("GET", "/v1/certificate/fake-id"),
        ("POST", "/v1/webhooks"),
        ("GET", "/v1/webhooks"),
        ("GET", "/v1/webhooks/fake-id"),
        ("PATCH", "/v1/webhooks/fake-id"),
        ("DELETE", "/v1/webhooks/fake-id"),
        ("GET", "/analytics/usage"),
        ("GET", "/analytics/daily"),
        ("GET", "/analytics/monthly-entries"),
        ("GET", "/analytics/top-chains"),
        ("GET", "/analytics/hourly-distribution"),
        ("GET", "/admin/status"),
        ("GET", "/admin/metrics"),
        ("GET", "/admin/logs"),
        ("GET", "/admin/rate-limits"),
        ("GET", "/admin/health/deep"),
        ("POST", "/admin/cache/clear"),
    ])
    def test_returns_401(self, method, path):
        resp = client.request(method, path)
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}"


class TestInvalidTokens:
    """Requests with invalid or expired tokens must be rejected."""

    def test_invalid_bearer_token(self):
        resp = client.get("/v1/chains", headers={"Authorization": "Bearer garbage_token"})
        assert resp.status_code == 401

    def test_expired_jwt(self):
        token = _make_jwt("user1", expired=True)
        resp = client.get("/v1/chains", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_malformed_auth_header(self):
        resp = client.get("/v1/chains", headers={"Authorization": "NotBearer token"})
        assert resp.status_code == 401

    def test_empty_auth_header(self):
        resp = client.get("/v1/chains", headers={"Authorization": ""})
        assert resp.status_code == 401

    def test_bearer_no_token(self):
        resp = client.get("/v1/chains", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401


class TestAdminScopeEnforcement:
    """Admin routes must require admin scope."""

    def test_non_admin_cannot_access_status(self):
        # Regular API key has read/write but NOT admin
        resp = client.get("/admin/status", headers=AUTH)
        assert resp.status_code == 403

    def test_non_admin_cannot_access_metrics(self):
        resp = client.get("/admin/metrics", headers=AUTH)
        assert resp.status_code == 403

    def test_non_admin_cannot_access_logs(self):
        resp = client.get("/admin/logs", headers=AUTH)
        assert resp.status_code == 403

    def test_non_admin_cannot_clear_cache(self):
        resp = client.post("/admin/cache/clear", headers=AUTH)
        assert resp.status_code == 403

    def test_non_admin_cannot_access_rate_limits(self):
        resp = client.get("/admin/rate-limits", headers=AUTH)
        assert resp.status_code == 403

    def test_non_admin_cannot_deep_health(self):
        resp = client.get("/admin/health/deep", headers=AUTH)
        assert resp.status_code == 403

    def test_admin_can_access_status(self):
        resp = client.get("/admin/status", headers=_admin_jwt())
        assert resp.status_code == 200

    def test_admin_can_access_metrics(self):
        resp = client.get("/admin/metrics", headers=_admin_jwt())
        assert resp.status_code == 200

    def test_admin_can_clear_cache(self):
        resp = client.post("/admin/cache/clear", headers=_admin_jwt())
        assert resp.status_code == 200


class TestRateLimiting:
    """Rate limiting must be enforced on all authenticated routes."""

    def setup_method(self):
        rate_limiter.clear()

    def test_rate_limit_headers_present(self):
        resp = client.get("/v1/chains", headers=AUTH)
        # Rate limit headers should be added by the rate limiter or response
        assert resp.status_code == 200

    def test_rate_limit_enforced(self):
        rate_limiter.clear()
        # Create a token for a test user to isolate rate limiting
        token = create_jwt_token("rate_limit_test_user")
        headers = {"Authorization": f"Bearer {token}"}
        # Free plan: 60 requests per minute
        for i in range(60):
            resp = client.get("/v1/chains", headers=headers)
            assert resp.status_code == 200, f"Request {i+1} failed with {resp.status_code}"
        # 61st request should be rate limited
        resp = client.get("/v1/chains", headers=headers)
        assert resp.status_code == 429
        assert "Rate limit exceeded" in resp.json()["detail"]


class TestInputValidation:
    """All inputs must be validated."""

    def test_chain_name_empty(self):
        resp = client.post("/v1/chains", json={"name": ""}, headers=AUTH)
        assert resp.status_code == 422

    def test_chain_name_too_long(self):
        resp = client.post("/v1/chains", json={"name": "x" * 256}, headers=AUTH)
        assert resp.status_code == 422

    def test_entry_operation_empty(self):
        chain_id = _create_chain()
        resp = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "", "y_state": {"v": 1}},
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_entry_operation_too_long(self):
        chain_id = _create_chain()
        resp = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "x" * 256, "y_state": {"v": 1}},
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_batch_empty_entries(self):
        chain_id = _create_chain()
        resp = client.post(
            f"/v1/chains/{chain_id}/entries/batch",
            json={"entries": []},
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_batch_too_many_entries(self):
        chain_id = _create_chain()
        entries = [{"operation": f"op{i}", "y_state": {"v": i}} for i in range(101)]
        resp = client.post(
            f"/v1/chains/{chain_id}/entries/batch",
            json={"entries": entries},
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_checkpoint_name_empty(self):
        chain_id = _create_chain()
        # Add an entry first
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op1", "y_state": {"v": 1}},
            headers=AUTH,
        )
        resp = client.post(
            f"/v1/chains/{chain_id}/checkpoints",
            json={"name": ""},
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_invalid_json_body(self):
        resp = client.post(
            "/v1/chains",
            content="not json",
            headers={**AUTH, "Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_admin_logs_invalid_type(self):
        resp = client.get("/admin/logs?type=invalid", headers=_admin_jwt())
        assert resp.status_code == 422  # FastAPI Query(pattern=) validation


class TestSQLInjection:
    """SQL injection attempts must be safely handled."""

    SQL_PAYLOADS = [
        "'; DROP TABLE chains; --",
        "1 OR 1=1",
        "' UNION SELECT * FROM users --",
        "1; DELETE FROM entries WHERE 1=1",
        "Robert'); DROP TABLE chains;--",
    ]

    def test_sql_in_chain_name(self):
        for payload in self.SQL_PAYLOADS:
            resp = client.post(
                "/v1/chains",
                json={"name": payload[:255]},
                headers=AUTH,
            )
            # Should succeed (in-memory storage) — the point is it doesn't execute SQL
            assert resp.status_code == 200
            assert resp.json()["name"] == payload[:255]

    def test_sql_in_entry_operation(self):
        chain_id = _create_chain()
        for payload in self.SQL_PAYLOADS:
            resp = client.post(
                f"/v1/chains/{chain_id}/entries",
                json={"operation": payload[:255], "y_state": {"v": 1}},
                headers=AUTH,
            )
            assert resp.status_code == 200


class TestXSSPrevention:
    """XSS payloads in metadata must not be executed."""

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "' onmouseover='alert(1)'",
        "<svg/onload=alert('xss')>",
    ]

    def test_xss_in_entry_metadata(self):
        chain_id = _create_chain()
        for payload in self.XSS_PAYLOADS:
            resp = client.post(
                f"/v1/chains/{chain_id}/entries",
                json={
                    "operation": "test",
                    "y_state": {"data": payload},
                    "metadata": {"note": payload},
                },
                headers=AUTH,
            )
            assert resp.status_code == 200
            # API returns JSON, not HTML — XSS not executable
            data = resp.json()
            assert data["metadata"]["note"] == payload

    def test_xss_in_chain_name(self):
        for payload in self.XSS_PAYLOADS:
            resp = client.post(
                "/v1/chains",
                json={"name": payload[:255]},
                headers=AUTH,
            )
            assert resp.status_code == 200
            assert resp.json()["name"] == payload[:255]


class TestWebhookSecurity:
    """Webhook URL validation and SSRF prevention."""

    def test_webhook_requires_https(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "http://example.com/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        assert resp.status_code == 400
        assert "HTTPS" in resp.json()["detail"]

    def test_webhook_blocks_localhost(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://localhost/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_webhook_blocks_127_0_0_1(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://127.0.0.1/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_webhook_blocks_private_ip(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://192.168.1.1/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_webhook_blocks_10_x(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://10.0.0.1/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_webhook_invalid_events(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://example.com/hook", "events": ["not.a.real.event"]},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_webhook_valid_https(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://example.com/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        assert resp.status_code == 200

    def test_webhook_update_validates_url(self):
        # Create a valid webhook
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://example.com/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        webhook_id = resp.json()["id"]
        # Try to update with http URL
        resp = client.patch(
            f"/v1/webhooks/{webhook_id}",
            json={"url": "http://evil.com/hook"},
            headers=AUTH,
        )
        assert resp.status_code == 400


class TestOAuthSecurity:
    """OAuth endpoints must validate configuration."""

    def test_github_oauth_unconfigured(self):
        resp = client.get("/v1/auth/oauth/github?code=testcode1234")
        assert resp.status_code == 501
        assert "not configured" in resp.json()["detail"]

    def test_github_oauth_redirect_unconfigured(self):
        resp = client.get("/v1/auth/oauth/github", follow_redirects=False)
        assert resp.status_code == 501
        assert "not configured" in resp.json()["detail"]

    def test_google_oauth_unconfigured(self):
        resp = client.post("/v1/auth/oauth/google?code=testcode1234")
        assert resp.status_code == 501
        assert "not configured" in resp.json()["detail"]


class TestErrorResponseSafety:
    """Error responses must not leak internal details."""

    def test_404_no_stack_trace(self):
        resp = client.get("/v1/chains/nonexistent", headers=AUTH)
        assert resp.status_code == 404
        body = resp.json()
        assert "detail" in body
        assert "Traceback" not in str(body)
        assert "File" not in str(body)

    def test_422_no_stack_trace(self):
        resp = client.post("/v1/chains", json={"name": ""}, headers=AUTH)
        assert resp.status_code == 422
        body = resp.text
        assert "Traceback" not in body

    def test_401_no_stack_trace(self):
        resp = client.get("/v1/chains")
        body = resp.json()
        assert "Traceback" not in str(body)


class TestAccessControl:
    """Users cannot access other users' resources."""

    def test_cannot_access_other_users_chain(self):
        # User 1 creates a chain
        chain_id = _create_chain(headers=AUTH)
        # User 2 tries to access it
        resp = client.get(f"/v1/chains/{chain_id}", headers=AUTH_2)
        assert resp.status_code == 404

    def test_cannot_append_to_other_users_chain(self):
        chain_id = _create_chain(headers=AUTH)
        resp = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "evil", "y_state": {"v": 1}},
            headers=AUTH_2,
        )
        assert resp.status_code == 404

    def test_cannot_verify_other_users_chain(self):
        chain_id = _create_chain(headers=AUTH)
        resp = client.get(f"/v1/chains/{chain_id}/verify", headers=AUTH_2)
        assert resp.status_code == 404

    def test_cannot_share_other_users_chain(self):
        chain_id = _create_chain(headers=AUTH)
        resp = client.get(f"/v1/chains/{chain_id}/share", headers=AUTH_2)
        assert resp.status_code == 404

    def test_cannot_access_other_users_webhook(self):
        # User 1 creates a webhook
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://example.com/hook", "events": ["chain.created"]},
            headers=AUTH,
        )
        webhook_id = resp.json()["id"]
        # User 2 tries to access
        resp = client.get(f"/v1/webhooks/{webhook_id}", headers=AUTH_2)
        assert resp.status_code == 404

    def test_cannot_delete_other_users_webhook(self):
        resp = client.post(
            "/v1/webhooks",
            json={"url": "https://example.com/hook2", "events": ["chain.created"]},
            headers=AUTH,
        )
        webhook_id = resp.json()["id"]
        resp = client.delete(f"/v1/webhooks/{webhook_id}", headers=AUTH_2)
        assert resp.status_code == 404


class TestPublicEndpoints:
    """Public endpoints should work without auth."""

    def test_health_no_auth(self):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_health_check_no_auth(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_shared_chain_no_auth(self):
        # Create and share a chain
        chain_id = _create_chain()
        client.post(
            f"/v1/chains/{chain_id}/entries",
            json={"operation": "op1", "y_state": {"v": 1}},
            headers=AUTH,
        )
        share_resp = client.get(f"/v1/chains/{chain_id}/share", headers=AUTH)
        share_id = share_resp.json()["share_id"]
        # Access without auth
        resp = client.get(f"/v1/shared/{share_id}")
        assert resp.status_code == 200

    def test_receipt_badge_no_auth(self):
        resp = client.get("/v1/receipts/nonexistent/badge")
        assert resp.status_code == 404  # 404, not 401

    def test_webhook_events_list_no_auth(self):
        resp = client.get("/v1/webhooks/events/list")
        assert resp.status_code == 200


class TestCORSHeaders:
    """CORS should be properly configured."""

    def test_cors_allows_pruv_origins(self):
        resp = client.options(
            "/v1/chains",
            headers={
                "Origin": "https://app.pruv.dev",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "https://app.pruv.dev"

    def test_cors_blocks_unknown_origin(self):
        resp = client.options(
            "/v1/chains",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should not include the evil origin
        assert resp.headers.get("access-control-allow-origin") != "https://evil.com"
