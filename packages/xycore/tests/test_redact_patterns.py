"""Exhaustive test: every required redaction pattern is caught by redact_state."""

import pytest

from xycore.redact import redact_state


class TestRedactAllRequiredPatterns:
    """Each of the 11 required patterns must be redacted."""

    def test_stripe_live_key(self):
        state = {"config": "stripe key sk_live_4eC39HqLyjWDarjtT1zdp7dc"}
        result = redact_state(state)
        assert "sk_live_" not in result["config"]
        assert "[REDACTED]" in result["config"]

    def test_stripe_test_key(self):
        state = {"config": "stripe key sk_test_4eC39HqLyjWDarjtT1zdp7dc"}
        result = redact_state(state)
        assert "sk_test_" not in result["config"]
        assert "[REDACTED]" in result["config"]

    def test_pruv_live_key(self):
        state = {"note": "pruv key pv_live_abc123def456"}
        result = redact_state(state)
        assert "pv_live_" not in result["note"]
        assert "[REDACTED]" in result["note"]

    def test_pruv_test_key(self):
        state = {"note": "pruv key pv_test_xyz789"}
        result = redact_state(state)
        assert "pv_test_" not in result["note"]
        assert "[REDACTED]" in result["note"]

    def test_github_personal_access_token(self):
        state = {"env": "GITHUB_TOKEN=ghp_ABCdef123456789012345678901234567890"}
        result = redact_state(state)
        assert "ghp_" not in result["env"]
        assert "[REDACTED]" in result["env"]

    def test_github_oauth_token(self):
        state = {"env": "token gho_ABCdef123456"}
        result = redact_state(state)
        assert "gho_" not in result["env"]
        assert "[REDACTED]" in result["env"]

    def test_aws_access_key(self):
        state = {"aws": "AKIAIOSFODNN7EXAMPLE"}
        result = redact_state(state)
        assert "AKIA" not in result["aws"]
        assert "[REDACTED]" in result["aws"]

    def test_password_equals(self):
        state = {"log": "connection password=SuperS3cret123"}
        result = redact_state(state)
        assert "SuperS3cret123" not in result["log"]
        assert "[REDACTED]" in result["log"]

    def test_api_key_equals(self):
        state = {"log": "config api_key=my_secret_key_value"}
        result = redact_state(state)
        assert "my_secret_key_value" not in result["log"]
        assert "[REDACTED]" in result["log"]

    def test_secret_equals(self):
        state = {"log": "secret=xyzzy12345"}
        result = redact_state(state)
        assert "xyzzy12345" not in result["log"]
        assert "[REDACTED]" in result["log"]

    def test_token_equals(self):
        state = {"log": "auth token=Bearer_abc123"}
        result = redact_state(state)
        assert "Bearer_abc123" not in result["log"]
        assert "[REDACTED]" in result["log"]


class TestRedactKeyBasedPatterns:
    """Keys named after secrets get their entire value replaced."""

    def test_password_key(self):
        state = {"password": "hunter2"}
        assert redact_state(state)["password"] == "[REDACTED]"

    def test_secret_key(self):
        state = {"client_secret": "abc123"}
        assert redact_state(state)["client_secret"] == "[REDACTED]"

    def test_api_key_key(self):
        state = {"api_key": "my-key-value"}
        assert redact_state(state)["api_key"] == "[REDACTED]"

    def test_token_key(self):
        state = {"auth_token": "jwt.token.here"}
        assert redact_state(state)["auth_token"] == "[REDACTED]"

    def test_database_url_key(self):
        state = {"database_url": "postgresql://user:pass@host/db"}
        assert redact_state(state)["database_url"] == "[REDACTED]"


class TestRedactNested:
    """Secrets are redacted at any nesting depth."""

    def test_deeply_nested(self):
        state = {"a": {"b": {"c": {"secret": "deep_value"}}}}
        result = redact_state(state)
        assert result["a"]["b"]["c"]["secret"] == "[REDACTED]"

    def test_list_of_dicts(self):
        state = {"items": [{"password": "p1"}, {"password": "p2"}]}
        result = redact_state(state)
        assert result["items"][0]["password"] == "[REDACTED]"
        assert result["items"][1]["password"] == "[REDACTED]"

    def test_mixed_safe_and_secret(self):
        state = {
            "name": "my-service",
            "version": "1.0",
            "api_key": "secret_val",
            "config": "key is sk_live_abc123",
        }
        result = redact_state(state)
        assert result["name"] == "my-service"
        assert result["version"] == "1.0"
        assert result["api_key"] == "[REDACTED]"
        assert "sk_live_" not in result["config"]


class TestRedactPreservesNonSecrets:
    """Non-secret values pass through unchanged."""

    def test_integers(self):
        assert redact_state({"count": 42}) == {"count": 42}

    def test_booleans(self):
        assert redact_state({"active": True}) == {"active": True}

    def test_none(self):
        assert redact_state({"val": None}) == {"val": None}

    def test_safe_strings(self):
        state = {"message": "Hello world", "status": "ok"}
        assert redact_state(state) == state
