"""Tests for pruv.identity — persistent verifiable identity for agents."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from pruv.identity import AgentIdentity, Identity, IdentityVerification


# Deterministic fake keypair for testing
FAKE_PRIVATE_KEY = b"\x01" * 32
FAKE_PUBLIC_KEY = b"\x02" * 32


@pytest.fixture
def mock_client():
    """Create an Identity instance with a mocked PruvClient."""
    with patch("pruv.identity.PruvClient") as MockClient, \
         patch("pruv.identity.generate_keypair", return_value=(FAKE_PRIVATE_KEY, FAKE_PUBLIC_KEY)):
        client_instance = MagicMock()
        MockClient.return_value = client_instance

        # Default chain creation response
        client_instance.create_chain.return_value = {"id": "chain_abc123"}

        # Default add_entry response
        client_instance.add_entry.return_value = {
            "id": "entry_001",
            "index": 0,
            "xy": "xy_deadbeef",
        }

        identity_mod = Identity(api_key="pv_test_xxx")
        yield identity_mod, client_instance


@pytest.fixture
def registered_identity(mock_client):
    """Register a test identity and return (Identity, AgentIdentity, mock_client)."""
    identity_mod, client_instance = mock_client
    agent = identity_mod.register("test-agent", agent_type="langchain")
    return identity_mod, agent, client_instance


def test_register_identity(mock_client):
    """Register returns AgentIdentity with address, public key, chain."""
    identity_mod, client_instance = mock_client

    agent = identity_mod.register("my-agent", agent_type="crewai")

    assert isinstance(agent, AgentIdentity)
    assert agent.name == "my-agent"
    assert agent.agent_type == "crewai"
    assert agent.address.startswith("pi_")
    assert len(agent.address) == 43  # pi_ + 40 hex chars
    assert len(agent.public_key) == 64  # 32 bytes hex
    assert agent.chain_id == "chain_abc123"
    assert agent.action_count == 0

    # Should have created chain with identity metadata
    client_instance.create_chain.assert_called_once()
    call_kwargs = client_instance.create_chain.call_args
    assert call_kwargs[1]["metadata"]["type"] == "identity"
    assert call_kwargs[1]["metadata"]["agent_name"] == "my-agent"

    # Should have added registration entry
    client_instance.add_entry.assert_called_once()


def test_register_with_metadata(mock_client):
    """Register passes through custom metadata."""
    identity_mod, client_instance = mock_client

    agent = identity_mod.register(
        "my-agent",
        agent_type="custom",
        metadata={"version": "2.0", "framework": "custom"},
    )

    call_kwargs = client_instance.create_chain.call_args
    assert call_kwargs[1]["metadata"]["version"] == "2.0"
    assert call_kwargs[1]["metadata"]["framework"] == "custom"


def test_act_records_action(registered_identity):
    """Action appends to identity chain."""
    identity_mod, agent, client_instance = registered_identity

    # Reset mock from registration calls
    client_instance.add_entry.reset_mock()
    client_instance.add_entry.return_value = {
        "id": "entry_002",
        "index": 1,
        "xy": "xy_cafebabe",
    }

    result = identity_mod.act(agent.id, "read_email", {"from": "boss@co.com"})

    assert result["id"] == "entry_002"
    assert agent.action_count == 1

    # Verify the entry was added to the correct chain
    call_args = client_instance.add_entry.call_args
    assert call_args[1]["chain_id"] == agent.chain_id
    assert call_args[1]["data"]["action"] == "read_email"
    assert call_args[1]["data"]["identity"] == agent.id


def test_act_increments_count(registered_identity):
    """Multiple actions increment the action count."""
    identity_mod, agent, client_instance = registered_identity

    client_instance.add_entry.return_value = {"id": "e", "index": 1, "xy": "xy_1"}
    identity_mod.act(agent.id, "action_1")
    assert agent.action_count == 1

    client_instance.add_entry.return_value = {"id": "e", "index": 2, "xy": "xy_2"}
    identity_mod.act(agent.id, "action_2")
    assert agent.action_count == 2

    client_instance.add_entry.return_value = {"id": "e", "index": 3, "xy": "xy_3"}
    identity_mod.act(agent.id, "action_3")
    assert agent.action_count == 3


def test_verify_intact(registered_identity):
    """Identity with actions verifies successfully."""
    identity_mod, agent, client_instance = registered_identity

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 4,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": agent.chain_id,
        "entries": [
            {"data": {"action": "identity.registered"}},
            {"data": {"action": "read_email", "ts": 1000.0}},
            {"data": {"action": "draft_reply", "ts": 1001.0}},
            {"data": {"action": "send_email", "ts": 1002.0}},
        ],
    }

    result = identity_mod.verify(agent.id)

    assert isinstance(result, IdentityVerification)
    assert result.valid is True
    assert result.chain_intact is True
    assert result.identity_id == agent.id
    assert result.name == agent.name


def test_verify_reports_action_count(registered_identity):
    """Action count excludes registration entry."""
    identity_mod, agent, client_instance = registered_identity

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 4,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": agent.chain_id,
        "entries": [
            {"data": {"action": "identity.registered"}},
            {"data": {"action": "a1", "ts": 1000.0}},
            {"data": {"action": "a2", "ts": 1001.0}},
            {"data": {"action": "a3", "ts": 1002.0}},
        ],
    }

    result = identity_mod.verify(agent.id)

    assert result.action_count == 3  # excludes registration
    assert result.first_action == 1000.0
    assert result.last_action == 1002.0


def test_verify_broken_chain(registered_identity):
    """Broken chain reports failure."""
    identity_mod, agent, client_instance = registered_identity

    client_instance.verify_chain.return_value = {
        "valid": False,
        "length": 3,
        "break_index": 2,
    }
    client_instance.get_chain.return_value = {
        "id": agent.chain_id,
        "entries": [
            {"data": {"action": "identity.registered"}},
            {"data": {"action": "a1", "ts": 1000.0}},
            {"data": {"action": "a2", "ts": 1001.0}},
        ],
    }

    result = identity_mod.verify(agent.id)

    assert result.valid is False
    assert result.chain_intact is False
    assert "failed" in result.message.lower() or "✗" in result.message


def test_receipt_schema(registered_identity):
    """Receipt matches universal schema with type='identity'."""
    identity_mod, agent, client_instance = registered_identity

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 2,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": agent.chain_id,
        "entries": [
            {"data": {"action": "identity.registered"}},
            {"data": {"action": "test_action", "ts": 1000.0}},
        ],
    }

    receipt = identity_mod.receipt(agent.id)

    assert receipt["pruv_version"] == "1.0"
    assert receipt["type"] == "identity"
    assert receipt["chain_id"] == agent.chain_id
    assert receipt["chain_intact"] is True
    assert "product_data" in receipt
    assert receipt["product_data"]["identity_id"] == agent.id
    assert receipt["product_data"]["name"] == agent.name
    assert receipt["product_data"]["agent_type"] == agent.agent_type
    assert receipt["product_data"]["public_key"] == agent.public_key
    assert receipt["product_data"]["address"] == agent.address
    assert receipt["product_data"]["action_count"] == 1


def test_history_returns_actions(registered_identity):
    """History returns actions most recent first, excludes registration."""
    identity_mod, agent, client_instance = registered_identity

    client_instance.get_chain.return_value = {
        "id": agent.chain_id,
        "entries": [
            {"data": {"action": "identity.registered"}},
            {"data": {"action": "first_action", "ts": 1000.0}},
            {"data": {"action": "second_action", "ts": 1001.0}},
            {"data": {"action": "third_action", "ts": 1002.0}},
        ],
    }

    history = identity_mod.history(agent.id)

    assert len(history) == 3
    # Most recent first
    assert history[0]["data"]["action"] == "third_action"
    assert history[1]["data"]["action"] == "second_action"
    assert history[2]["data"]["action"] == "first_action"


def test_history_limit(registered_identity):
    """History respects limit parameter."""
    identity_mod, agent, client_instance = registered_identity

    client_instance.get_chain.return_value = {
        "id": agent.chain_id,
        "entries": [
            {"data": {"action": "identity.registered"}},
            {"data": {"action": "a1", "ts": 1000.0}},
            {"data": {"action": "a2", "ts": 1001.0}},
            {"data": {"action": "a3", "ts": 1002.0}},
        ],
    }

    history = identity_mod.history(agent.id, limit=2)

    assert len(history) == 2


def test_unknown_identity_raises(mock_client):
    """KeyError for unregistered identity."""
    identity_mod, _ = mock_client

    with pytest.raises(KeyError, match="Identity not found"):
        identity_mod.act("pi_nonexistent", "do_something")

    with pytest.raises(KeyError, match="Identity not found"):
        identity_mod.verify("pi_nonexistent")

    with pytest.raises(KeyError, match="Identity not found"):
        identity_mod.receipt("pi_nonexistent")

    with pytest.raises(KeyError, match="Identity not found"):
        identity_mod.history("pi_nonexistent")


def test_lookup(registered_identity):
    """Lookup returns registered identity or None."""
    identity_mod, agent, _ = registered_identity

    found = identity_mod.lookup(agent.id)
    assert found is not None
    assert found.name == agent.name

    not_found = identity_mod.lookup("pi_nonexistent")
    assert not_found is None


def test_fingerprint(registered_identity):
    """Fingerprint is first 12 chars of address."""
    _, agent, _ = registered_identity

    assert agent.fingerprint == agent.address[:12]
    assert agent.fingerprint.startswith("pi_")
