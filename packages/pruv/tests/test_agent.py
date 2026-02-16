"""Tests for pruv Agent and PruvClient."""

import hashlib
import json
from unittest.mock import MagicMock, patch

import pytest

from pruv.agent import Agent, ActionError
from pruv.client import PruvClient


# ------------------------------------------------------------------ #
# PruvClient
# ------------------------------------------------------------------ #


class TestPruvClient:
    """Unit tests for the synchronous HTTP client."""

    def _make_client(self) -> PruvClient:
        return PruvClient(api_key="pv_test_abc123", endpoint="https://api.pruv.dev")

    def test_init_sets_headers(self):
        client = self._make_client()
        assert client.api_key == "pv_test_abc123"
        assert client.endpoint == "https://api.pruv.dev"
        h = client._http.headers
        assert h["Authorization"] == "Bearer pv_test_abc123"
        assert h["Content-Type"] == "application/json"
        client.close()

    def test_endpoint_trailing_slash_stripped(self):
        client = PruvClient(api_key="k", endpoint="https://api.pruv.dev/")
        assert client.endpoint == "https://api.pruv.dev"
        client.close()

    def test_context_manager(self):
        with PruvClient(api_key="k") as client:
            assert isinstance(client, PruvClient)
        # should not raise after __exit__


# ------------------------------------------------------------------ #
# Agent — mock PruvClient at the network boundary
# ------------------------------------------------------------------ #


def _mock_client() -> MagicMock:
    """Return a MagicMock that behaves like PruvClient."""
    mock = MagicMock(spec=PruvClient)
    mock.create_chain.return_value = {"id": "chain-001", "name": "test"}
    mock.add_entry.return_value = {
        "id": "entry-001",
        "hash": "xy_" + "a" * 64,
        "index": 0,
    }
    mock.verify_chain.return_value = {"verified": True, "entries": 2}
    mock.get_chain.return_value = {
        "id": "chain-001",
        "entries": [{"index": 0}, {"index": 1}],
    }
    mock.get_entry.return_value = {"id": "entry-001", "index": 0}
    mock.export_chain.return_value = "<html>...</html>"
    return mock


class TestAgent:
    """Tests for the Agent wrapper."""

    def _make_agent(self, mock: MagicMock | None = None) -> Agent:
        mock = mock or _mock_client()
        with patch("pruv.agent.PruvClient", return_value=mock):
            agent = Agent(
                name="test-agent",
                api_key="pv_test_abc123",
                metadata={"env": "test"},
            )
        return agent

    # -- init --------------------------------------------------------

    def test_init_creates_chain(self):
        mock = _mock_client()
        agent = self._make_agent(mock)
        mock.create_chain.assert_called_once()
        call_kwargs = mock.create_chain.call_args
        assert "test-agent" in call_kwargs.kwargs["name"]
        assert call_kwargs.kwargs["metadata"]["agent"] == "test-agent"
        assert call_kwargs.kwargs["metadata"]["env"] == "test"

    def test_init_sets_attributes(self):
        agent = self._make_agent()
        assert agent.name == "test-agent"
        assert agent.metadata == {"env": "test"}
        assert agent._action_count == 0

    # -- action ------------------------------------------------------

    def test_action_records_entry(self):
        mock = _mock_client()
        agent = self._make_agent(mock)
        result = agent.action("read_email", {"from": "a@b.com"})
        mock.add_entry.assert_called_once()
        entry_data = mock.add_entry.call_args.kwargs["data"]
        assert entry_data["action"] == "read_email"
        assert entry_data["seq"] == 1
        assert entry_data["data"]["from"] == "a@b.com"
        assert result["id"] == "entry-001"

    def test_action_increments_seq(self):
        mock = _mock_client()
        agent = self._make_agent(mock)
        agent.action("a", {"x": 1})
        agent.action("b", {"x": 2})
        agent.action("c", {"x": 3})
        assert agent._action_count == 3
        calls = mock.add_entry.call_args_list
        seqs = [c.kwargs["data"]["seq"] for c in calls]
        assert seqs == [1, 2, 3]

    # -- redaction ---------------------------------------------------

    def test_redact_replaces_sensitive_keys(self):
        agent = self._make_agent()
        data = {"password": "secret123", "user": "alice"}
        redacted = agent._redact(data, ["password"])
        assert redacted["user"] == "alice"
        assert redacted["password"]["_redacted"] is True
        expected_hash = hashlib.sha256(b"secret123").hexdigest()
        assert redacted["password"]["_hash"] == expected_hash

    def test_redact_hashes_non_string_values(self):
        agent = self._make_agent()
        data = {"config": {"a": 1, "b": 2}}
        redacted = agent._redact(data, ["config"])
        assert redacted["config"]["_redacted"] is True
        raw = json.dumps({"a": 1, "b": 2}, sort_keys=True)
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert redacted["config"]["_hash"] == expected

    def test_redact_noop_when_no_keys(self):
        agent = self._make_agent()
        data = {"x": 1, "y": 2}
        assert agent._redact(data, []) is data  # same object returned

    # -- verify / chain / receipt / export ---------------------------

    def test_verify(self):
        mock = _mock_client()
        agent = self._make_agent(mock)
        result = agent.verify()
        mock.verify_chain.assert_called_once_with("chain-001")
        assert result["verified"] is True

    def test_chain(self):
        mock = _mock_client()
        agent = self._make_agent(mock)
        result = agent.chain()
        mock.get_chain.assert_called_once_with("chain-001")
        assert len(result["entries"]) == 2

    def test_receipt(self):
        mock = _mock_client()
        agent = self._make_agent(mock)
        result = agent.receipt("entry-001")
        mock.get_entry.assert_called_once_with("chain-001", "entry-001")
        assert result["id"] == "entry-001"

    def test_export(self):
        mock = _mock_client()
        agent = self._make_agent(mock)
        html = agent.export()
        mock.export_chain.assert_called_once_with("chain-001")
        assert "<html>" in html


class TestActionError:
    def test_is_exception(self):
        err = ActionError("boom")
        assert isinstance(err, Exception)
        assert str(err) == "boom"
