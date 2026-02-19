"""Tests for pruv.provenance — origin and chain of custody for digital artifacts."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from pruv.provenance import Artifact, Provenance, ProvenanceVerification, _hash_content


@pytest.fixture
def mock_client():
    """Create a Provenance instance with a mocked PruvClient."""
    with patch("pruv.provenance.PruvClient") as MockClient:
        client_instance = MagicMock()
        MockClient.return_value = client_instance

        # Default chain creation response
        client_instance.create_chain.return_value = {"id": "chain_prov_001"}

        # Default add_entry response
        client_instance.add_entry.return_value = {
            "id": "entry_001",
            "index": 0,
            "xy": "xy_deadbeef",
        }

        prov = Provenance(api_key="pv_test_xxx")
        yield prov, client_instance


@pytest.fixture
def registered_artifact(mock_client):
    """Register a test artifact and return (Provenance, Artifact, mock_client)."""
    prov, client_instance = mock_client
    artifact = prov.origin(
        content=b"Original contract text here",
        name="contract-v1.pdf",
        creator="legal@acme.com",
        content_type="application/pdf",
    )
    return prov, artifact, client_instance


def test_hash_content_bytes():
    """_hash_content works with bytes."""
    result = _hash_content(b"hello world")
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert result == expected


def test_hash_content_string():
    """_hash_content works with strings."""
    result = _hash_content("hello world")
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert result == expected


def test_origin_creates_artifact(mock_client):
    """Origin returns Artifact with hash and chain."""
    prov, client_instance = mock_client

    artifact = prov.origin(
        content=b"Original content",
        name="doc.pdf",
        creator="alice@co.com",
        content_type="application/pdf",
    )

    assert isinstance(artifact, Artifact)
    assert artifact.name == "doc.pdf"
    assert artifact.creator == "alice@co.com"
    assert artifact.content_type == "application/pdf"
    assert artifact.id.startswith("pa_")
    assert len(artifact.id) == 43  # pa_ + 40 hex chars
    assert artifact.chain_id == "chain_prov_001"
    assert artifact.transition_count == 0
    assert artifact.content_hash == artifact.current_hash

    # Verify the hash is correct
    expected_hash = hashlib.sha256(b"Original content").hexdigest()
    assert artifact.content_hash == expected_hash

    # Should have created chain with provenance metadata
    client_instance.create_chain.assert_called_once()
    call_kwargs = client_instance.create_chain.call_args
    assert call_kwargs[1]["metadata"]["type"] == "provenance"
    assert call_kwargs[1]["metadata"]["artifact_name"] == "doc.pdf"
    assert call_kwargs[1]["metadata"]["origin_hash"] == expected_hash

    # Should have added origin entry
    client_instance.add_entry.assert_called_once()


def test_origin_with_metadata(mock_client):
    """Origin passes through custom metadata."""
    prov, client_instance = mock_client

    artifact = prov.origin(
        content=b"test",
        name="test.txt",
        creator="bob",
        metadata={"department": "legal", "classification": "confidential"},
    )

    call_kwargs = client_instance.create_chain.call_args
    assert call_kwargs[1]["metadata"]["department"] == "legal"
    assert call_kwargs[1]["metadata"]["classification"] == "confidential"


def test_origin_with_string_content(mock_client):
    """Origin works with string content."""
    prov, _ = mock_client

    artifact = prov.origin(
        content="Plain text document",
        name="readme.txt",
        creator="dev@co.com",
    )

    expected_hash = hashlib.sha256(b"Plain text document").hexdigest()
    assert artifact.content_hash == expected_hash


def test_transition_records_modification(registered_artifact):
    """Transition appends with previous_hash -> new_hash."""
    prov, artifact, client_instance = registered_artifact

    # Reset mock from origin calls
    client_instance.add_entry.reset_mock()
    client_instance.add_entry.return_value = {
        "id": "entry_002",
        "index": 1,
        "xy": "xy_cafebabe",
    }

    result = prov.transition(
        artifact.id,
        content=b"Updated contract with clause 4.2",
        modifier="counsel@partner.com",
        reason="Added clause 4.2",
    )

    assert result["id"] == "entry_002"
    assert artifact.transition_count == 1

    # Verify the entry data
    call_args = client_instance.add_entry.call_args
    entry_data = call_args[1]["data"]
    assert entry_data["action"] == "provenance.transition"
    assert entry_data["artifact_id"] == artifact.id
    assert entry_data["previous_hash"] == artifact.content_hash  # original hash
    assert entry_data["modifier"] == "counsel@partner.com"
    assert entry_data["reason"] == "Added clause 4.2"

    # Current hash should be updated
    new_expected = hashlib.sha256(b"Updated contract with clause 4.2").hexdigest()
    assert artifact.current_hash == new_expected


def test_transition_chains_hashes(registered_artifact):
    """Multiple transitions chain previous_hash correctly."""
    prov, artifact, client_instance = registered_artifact

    original_hash = artifact.content_hash

    # First transition
    client_instance.add_entry.return_value = {"id": "e1", "index": 1, "xy": "xy_1"}
    prov.transition(artifact.id, content=b"version 2", modifier="alice")
    hash_v2 = artifact.current_hash

    # Second transition
    client_instance.add_entry.reset_mock()
    client_instance.add_entry.return_value = {"id": "e2", "index": 2, "xy": "xy_2"}
    prov.transition(artifact.id, content=b"version 3", modifier="bob")

    # The second transition should reference hash_v2 as previous
    call_args = client_instance.add_entry.call_args
    assert call_args[1]["data"]["previous_hash"] == hash_v2
    assert artifact.transition_count == 2


def test_verify_intact(registered_artifact):
    """Unmodified artifact verifies with origin_intact=True."""
    prov, artifact, client_instance = registered_artifact

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 1,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {
                "data": {
                    "action": "provenance.origin",
                    "content_hash": artifact.content_hash,
                }
            },
        ],
    }

    result = prov.verify(artifact.id)

    assert isinstance(result, ProvenanceVerification)
    assert result.valid is True
    assert result.origin_intact is True
    assert result.chain_intact is True
    assert result.transition_count == 0
    assert result.current_hash == artifact.current_hash


def test_verify_after_modifications(registered_artifact):
    """Modified artifact verifies with correct transition count."""
    prov, artifact, client_instance = registered_artifact

    # Simulate a transition
    client_instance.add_entry.return_value = {"id": "e1", "index": 1, "xy": "xy_1"}
    prov.transition(artifact.id, content=b"Modified content", modifier="alice")
    new_hash = _hash_content(b"Modified content")

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 2,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {
                "data": {
                    "action": "provenance.origin",
                    "content_hash": artifact.content_hash,
                }
            },
            {
                "data": {
                    "action": "provenance.transition",
                    "previous_hash": artifact.content_hash,
                    "new_hash": new_hash,
                }
            },
        ],
    }

    result = prov.verify(artifact.id)

    assert result.valid is True
    assert result.origin_intact is True
    assert result.transition_count == 1
    assert "1 modification" in result.message


def test_verify_detects_hash_mismatch(registered_artifact):
    """Tampering with transition hashes causes verification failure."""
    prov, artifact, client_instance = registered_artifact

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 2,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {
                "data": {
                    "action": "provenance.origin",
                    "content_hash": artifact.content_hash,
                }
            },
            {
                "data": {
                    "action": "provenance.transition",
                    "previous_hash": "tampered_hash_value",  # WRONG
                    "new_hash": "some_new_hash",
                }
            },
        ],
    }

    result = prov.verify(artifact.id)

    assert result.valid is False
    assert "transition hash mismatch" in result.message


def test_verify_detects_origin_tamper(registered_artifact):
    """Tampered origin entry causes verification failure."""
    prov, artifact, client_instance = registered_artifact

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 1,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {
                "data": {
                    "action": "provenance.origin",
                    "content_hash": "wrong_origin_hash",  # tampered
                }
            },
        ],
    }

    result = prov.verify(artifact.id)

    assert result.valid is False
    assert result.origin_intact is False
    assert "origin tampered" in result.message


def test_verify_broken_chain(registered_artifact):
    """Broken chain link causes verification failure."""
    prov, artifact, client_instance = registered_artifact

    client_instance.verify_chain.return_value = {
        "valid": False,
        "length": 2,
        "break_index": 1,
    }
    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {
                "data": {
                    "action": "provenance.origin",
                    "content_hash": artifact.content_hash,
                }
            },
            {
                "data": {
                    "action": "provenance.transition",
                    "previous_hash": artifact.content_hash,
                    "new_hash": "abc",
                }
            },
        ],
    }

    result = prov.verify(artifact.id)

    assert result.valid is False
    assert result.chain_intact is False
    assert "chain broken" in result.message


def test_receipt_schema(registered_artifact):
    """Receipt matches universal schema with type='provenance'."""
    prov, artifact, client_instance = registered_artifact

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 1,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {
                "data": {
                    "action": "provenance.origin",
                    "content_hash": artifact.content_hash,
                }
            },
        ],
    }

    receipt = prov.receipt(artifact.id)

    assert receipt["pruv_version"] == "1.0"
    assert receipt["type"] == "provenance"
    assert receipt["chain_id"] == artifact.chain_id
    assert receipt["chain_intact"] is True
    assert "product_data" in receipt

    pd = receipt["product_data"]
    assert pd["artifact_id"] == artifact.id
    assert pd["name"] == artifact.name
    assert pd["content_type"] == artifact.content_type
    assert pd["creator"] == artifact.creator
    assert pd["origin_hash"] == artifact.content_hash
    assert pd["current_hash"] == artifact.current_hash
    assert pd["origin_intact"] is True
    assert pd["transition_count"] == 0


def test_receipt_includes_modifications(registered_artifact):
    """Receipt product_data includes modification timeline."""
    prov, artifact, client_instance = registered_artifact

    new_hash = _hash_content(b"Updated")

    client_instance.verify_chain.return_value = {
        "valid": True,
        "length": 2,
        "break_index": None,
    }
    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {
                "data": {
                    "action": "provenance.origin",
                    "content_hash": artifact.content_hash,
                }
            },
            {
                "data": {
                    "action": "provenance.transition",
                    "previous_hash": artifact.content_hash,
                    "new_hash": new_hash,
                    "modifier": "alice@co.com",
                    "reason": "Fixed typo",
                    "ts": 1700000000.0,
                }
            },
        ],
    }

    # Need to simulate the transition so current_hash matches
    client_instance.add_entry.return_value = {"id": "e1", "index": 1, "xy": "xy_1"}
    prov.transition(artifact.id, content=b"Updated", modifier="alice@co.com", reason="Fixed typo")

    receipt = prov.receipt(artifact.id)
    mods = receipt["product_data"]["modifications"]

    assert len(mods) == 1
    assert mods[0]["modifier"] == "alice@co.com"
    assert mods[0]["reason"] == "Fixed typo"
    assert mods[0]["timestamp"] == 1700000000.0


def test_unknown_artifact_raises(mock_client):
    """KeyError for unregistered artifact."""
    prov, _ = mock_client

    with pytest.raises(KeyError, match="Artifact not found"):
        prov.transition("pa_nonexistent", content=b"x", modifier="x")

    with pytest.raises(KeyError, match="Artifact not found"):
        prov.verify("pa_nonexistent")

    with pytest.raises(KeyError, match="Artifact not found"):
        prov.receipt("pa_nonexistent")

    with pytest.raises(KeyError, match="Artifact not found"):
        prov.history("pa_nonexistent")


def test_content_not_stored(mock_client):
    """Verify that actual content bytes are never sent to API.

    Only hashes are transmitted — the content stays with the owner.
    """
    prov, client_instance = mock_client

    artifact = prov.origin(
        content=b"Super secret document content",
        name="secret.pdf",
        creator="admin",
    )

    # Check create_chain call — should have hash, not content
    chain_call = client_instance.create_chain.call_args
    chain_meta = chain_call[1]["metadata"]
    assert "origin_hash" in chain_meta
    assert b"Super secret" not in str(chain_meta).encode()

    # Check add_entry call — should have hash, not content
    entry_call = client_instance.add_entry.call_args
    entry_data = entry_call[1]["data"]
    assert "content_hash" in entry_data
    assert b"Super secret" not in str(entry_data).encode()

    # Now do a transition
    client_instance.add_entry.reset_mock()
    client_instance.add_entry.return_value = {"id": "e1", "index": 1, "xy": "xy_1"}
    prov.transition(artifact.id, content=b"Updated secret content", modifier="admin")

    # Transition entry should only have hashes
    trans_call = client_instance.add_entry.call_args
    trans_data = trans_call[1]["data"]
    assert "previous_hash" in trans_data
    assert "new_hash" in trans_data
    assert b"Updated secret" not in str(trans_data).encode()


def test_lookup(registered_artifact):
    """Lookup returns registered artifact or None."""
    prov, artifact, _ = registered_artifact

    found = prov.lookup(artifact.id)
    assert found is not None
    assert found.name == artifact.name

    not_found = prov.lookup("pa_nonexistent")
    assert not_found is None


def test_fingerprint(registered_artifact):
    """Fingerprint is first 14 chars of artifact ID."""
    _, artifact, _ = registered_artifact

    assert artifact.fingerprint == artifact.id[:14]
    assert artifact.fingerprint.startswith("pa_")


def test_history(registered_artifact):
    """History returns all entries including origin."""
    prov, artifact, client_instance = registered_artifact

    client_instance.get_chain.return_value = {
        "id": artifact.chain_id,
        "entries": [
            {"data": {"action": "provenance.origin"}},
            {"data": {"action": "provenance.transition", "modifier": "alice"}},
        ],
    }

    history = prov.history(artifact.id)

    assert len(history) == 2
    assert history[0]["data"]["action"] == "provenance.origin"
    assert history[1]["data"]["action"] == "provenance.transition"
