"""Tests for pruv.provenance — the new implementation with agent references,
cross-product verification, and human-readable receipts.

Test cases from the spec:

Provenance tests:
1. Origin — chain has exactly one entry, X is null, content hash correct
2. Transition with valid agent — agent_in_scope True
3. Transition with expired agent — unauthorized_transitions populated
4. Transition with revoked agent — unauthorized_transitions populated
5. Verify intact chain — all counts correct, all agent references resolve
6. Verify broken chain — break_at correct, break_at_agent populated
7. Tamper detection — modify stored state, verify catches it at correct entry
8. Receipt format — all transitions listed, agent details present, human readable

Cross-product tests:
9.  Provenance receipt pulls identity chain for each agent
10. If identity chain is broken, provenance flags that transition as unauthorized
11. Revoked agent shows as unauthorized in provenance even if action hash is intact
"""

import json
import sqlite3

import pytest

import pruv.identity as identity
import pruv.provenance as provenance
from pruv.provenance import (
    Artifact,
    ProvenanceVerificationResult,
    Transition,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolated_dbs(tmp_path):
    """Each test gets its own SQLite databases for both products."""
    identity.configure(db_path=str(tmp_path / "identity.db"))
    provenance.configure(db_path=str(tmp_path / "provenance.db"))
    yield tmp_path
    identity._reset()
    provenance._reset()


@pytest.fixture
def agent():
    """Register a default test agent."""
    return identity.register(
        name="test-agent",
        framework="custom",
        owner="test-org",
        scope=["file.read", "file.write", "document.edit"],
        purpose="Automated testing",
        valid_until="2099-12-31",
    )


@pytest.fixture
def artifact():
    """Create a default test artifact."""
    return provenance.origin(
        content=b"original document content",
        name="test-document",
        classification="document",
        owner="test-org",
    )


# ─── 1. Origin ──────────────────────────────────────────────────────────────


class TestOrigin:
    def test_origin_returns_artifact(self):
        art = provenance.origin(
            content=b"hello world",
            name="test.txt",
            classification="document",
            owner="acme",
        )
        assert isinstance(art, Artifact)
        assert art.name == "test.txt"
        assert art.classification == "document"
        assert art.owner == "acme"
        assert art.id  # uuid present
        assert art.chain_id  # chain id present
        assert art.origin_hash  # content hash present
        assert art.current_state_hash == art.origin_hash

    def test_origin_chain_has_one_entry(self):
        art = provenance.origin(
            content=b"content",
            name="single-entry",
            classification="code",
            owner="test",
        )
        result = provenance.verify(art.id)
        assert result.entries == 1

    def test_origin_first_entry_x_is_null(self):
        art = provenance.origin(
            content=b"content",
            name="genesis-test",
            classification="document",
            owner="test",
        )
        from pruv.provenance import _get_registry

        _, chain = _get_registry().load(art.id)
        entry = chain.entries[0]
        assert entry.x == "GENESIS"
        assert entry.x_state is None

    def test_origin_content_hash_correct(self):
        import hashlib

        content = b"deterministic content"
        expected_hash = hashlib.sha256(content).hexdigest()
        art = provenance.origin(
            content=content,
            name="hash-test",
            classification="dataset",
            owner="test",
        )
        assert art.origin_hash == expected_hash
        assert art.current_state_hash == expected_hash

    def test_origin_string_content(self):
        import hashlib

        content = "string content"
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        art = provenance.origin(
            content=content,
            name="string-test",
            classification="document",
            owner="test",
        )
        assert art.origin_hash == expected_hash

    def test_origin_dict_content(self):
        import hashlib
        import json as json_mod

        content = {"key": "value", "nested": [1, 2, 3]}
        canonical = json_mod.dumps(content, sort_keys=True, separators=(",", ":"))
        expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        art = provenance.origin(
            content=content,
            name="dict-test",
            classification="dataset",
            owner="test",
        )
        assert art.origin_hash == expected_hash

    def test_origin_y_state_contains_metadata(self):
        art = provenance.origin(
            content=b"content",
            name="meta-test",
            classification="document",
            owner="test",
            metadata={"version": "1.0"},
        )
        from pruv.provenance import _get_registry

        _, chain = _get_registry().load(art.id)
        y_state = chain.entries[0].y_state
        assert y_state["event"] == "origin"
        assert y_state["name"] == "meta-test"
        assert y_state["metadata"] == {"version": "1.0"}


# ─── 2. Transition with valid agent ─────────────────────────────────────────


class TestTransitionValidAgent:
    def test_transition_returns_transition(self, agent, artifact):
        t = provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"modified content",
            agent_id=agent.id,
            reason="Initial revision",
        )
        assert isinstance(t, Transition)
        assert t.artifact_id == artifact.id
        assert t.agent_id == agent.id
        assert t.agent_name == "test-agent"
        assert t.agent_owner == "test-org"
        assert t.agent_in_scope is True
        assert t.reason == "Initial revision"
        assert t.entry_index == 1

    def test_transition_updates_current_hash(self, agent, artifact):
        import hashlib

        new_content = b"updated content"
        expected_hash = hashlib.sha256(new_content).hexdigest()
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=new_content,
            agent_id=agent.id,
            reason="Update",
        )
        from pruv.provenance import _get_registry

        loaded = _get_registry().load(artifact.id)
        art, _ = loaded
        assert art.current_state_hash == expected_hash

    def test_transition_chains_hashes(self, agent, artifact):
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"version 2",
            agent_id=agent.id,
            reason="V2",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"version 3",
            agent_id=agent.id,
            reason="V3",
        )
        result = provenance.verify(artifact.id)
        assert result.entries == 3
        assert result.intact is True
        assert len(result.transitions) == 2


# ─── 3. Transition with expired agent ───────────────────────────────────────


class TestTransitionExpiredAgent:
    def test_expired_agent_flagged_unauthorized(self, artifact):
        expired = identity.register(
            name="expired-agent",
            framework="custom",
            owner="test-org",
            scope=["document.edit"],
            purpose="Testing",
            valid_from="2020-01-01",
            valid_until="2020-12-31",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"modified by expired",
            agent_id=expired.id,
            reason="Expired agent edit",
        )
        result = provenance.verify(artifact.id)
        assert len(result.unauthorized_transitions) == 1
        assert result.unauthorized_transitions[0].agent_name == "expired-agent"


# ─── 4. Transition with revoked agent ───────────────────────────────────────


class TestTransitionRevokedAgent:
    def test_revoked_agent_flagged_unauthorized(self, artifact):
        agent = identity.register(
            name="soon-revoked",
            framework="custom",
            owner="test-org",
            scope=["document.edit"],
            purpose="Testing",
            valid_until="2099-12-31",
        )
        # Make a valid transition first
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"valid edit",
            agent_id=agent.id,
            reason="Before revocation",
        )
        # Revoke the agent
        identity.revoke(agent.id, reason="No longer trusted")
        # Make another transition with revoked agent
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"revoked edit",
            agent_id=agent.id,
            reason="After revocation",
        )
        result = provenance.verify(artifact.id)
        # Both transitions should now be flagged since agent is revoked
        # (verify re-checks agent at query time)
        assert len(result.unauthorized_transitions) == 2
        assert result.intact is True  # chain itself is still intact


# ─── 5. Verify intact chain ─────────────────────────────────────────────────


class TestVerifyIntact:
    def test_verify_origin_only(self, artifact):
        result = provenance.verify(artifact.id)
        assert isinstance(result, ProvenanceVerificationResult)
        assert result.intact is True
        assert result.entries == 1
        assert result.verified_count == 1
        assert result.break_at is None
        assert result.break_detail is None
        assert len(result.transitions) == 0

    def test_verify_with_transitions(self, agent, artifact):
        for i in range(3):
            provenance.transition(
                artifact_id=artifact.id,
                updated_content=f"version {i + 2}".encode(),
                agent_id=agent.id,
                reason=f"Edit {i + 1}",
            )
        result = provenance.verify(artifact.id)
        assert result.intact is True
        assert result.entries == 4  # 1 origin + 3 transitions
        assert result.verified_count == 4
        assert len(result.transitions) == 3
        # All transitions should have valid agent references
        for t in result.transitions:
            assert t.agent_name == "test-agent"
            assert t.agent_owner == "test-org"
            assert t.agent_in_scope is True

    def test_verify_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            provenance.verify("nonexistent-id")


# ─── 6. Verify broken chain ─────────────────────────────────────────────────


class TestVerifyBroken:
    def test_broken_chain_detected(self, agent, artifact):
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"edit 1",
            agent_id=agent.id,
            reason="First edit",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"edit 2",
            agent_id=agent.id,
            reason="Second edit",
        )
        # Tamper with chain
        from pruv.provenance import _get_registry

        registry = _get_registry()
        with sqlite3.connect(registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM artifacts WHERE id = ?",
                (artifact.id,),
            ).fetchone()
            chain_data = json.loads(row[0])
            chain_data["entries"][1]["y"] = "tampered_hash"
            conn.execute(
                "UPDATE artifacts SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), artifact.id),
            )
        result = provenance.verify(artifact.id)
        assert result.intact is False
        assert result.break_at is not None

    def test_break_at_agent_populated(self, agent, artifact):
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"edit",
            agent_id=agent.id,
            reason="Edit",
        )
        # Tamper at the transition entry (index 1)
        from pruv.provenance import _get_registry

        registry = _get_registry()
        with sqlite3.connect(registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM artifacts WHERE id = ?",
                (artifact.id,),
            ).fetchone()
            chain_data = json.loads(row[0])
            chain_data["entries"][1]["y"] = "tampered"
            conn.execute(
                "UPDATE artifacts SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), artifact.id),
            )
        result = provenance.verify(artifact.id)
        assert result.intact is False
        assert result.break_at == 1
        assert result.break_at_agent == "test-agent"
        assert result.break_detail is not None
        assert "expected_x" in result.break_detail
        assert "found_x" in result.break_detail


# ─── 7. Tamper detection ────────────────────────────────────────────────────


class TestTamperDetection:
    def test_tamper_at_specific_entry(self, agent, artifact):
        for i in range(5):
            provenance.transition(
                artifact_id=artifact.id,
                updated_content=f"version {i + 2}".encode(),
                agent_id=agent.id,
                reason=f"Edit {i + 1}",
            )
        # Tamper with entry 3
        from pruv.provenance import _get_registry

        registry = _get_registry()
        with sqlite3.connect(registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM artifacts WHERE id = ?",
                (artifact.id,),
            ).fetchone()
            chain_data = json.loads(row[0])
            chain_data["entries"][3]["y"] = "tampered_at_3"
            conn.execute(
                "UPDATE artifacts SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), artifact.id),
            )
        result = provenance.verify(artifact.id)
        assert result.intact is False
        assert result.break_at == 3
        assert result.verified_count == 3

    def test_origin_tamper_detected(self, artifact):
        from pruv.provenance import _get_registry

        registry = _get_registry()
        with sqlite3.connect(registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM artifacts WHERE id = ?",
                (artifact.id,),
            ).fetchone()
            chain_data = json.loads(row[0])
            chain_data["entries"][0]["y"] = "tampered_origin"
            conn.execute(
                "UPDATE artifacts SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), artifact.id),
            )
        result = provenance.verify(artifact.id)
        assert result.intact is False
        assert result.break_at == 0


# ─── 8. Receipt format ──────────────────────────────────────────────────────


class TestReceipt:
    def test_receipt_universal_schema(self, agent, artifact):
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"edited",
            agent_id=agent.id,
            reason="Review",
        )
        r = provenance.receipt(artifact.id)
        assert r["pruv_version"] == "1.0"
        assert r["type"] == "provenance"
        assert r["chain_id"] == artifact.chain_id
        assert r["chain_intact"] is True
        assert r["entries"] == 2
        assert r["verified"] == "2/2"
        assert r["XY"].startswith("xy_")
        assert r["timestamp"]

    def test_receipt_product_data_transitions(self, agent, artifact):
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"version 2",
            agent_id=agent.id,
            reason="Section 1 revised",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"version 3",
            agent_id=agent.id,
            reason="Final edits",
        )
        r = provenance.receipt(artifact.id)
        pd = r["product_data"]
        assert pd["artifact_name"] == "test-document"
        assert pd["classification"] == "document"
        assert pd["owner"] == "test-org"
        assert pd["origin_hash"] == artifact.origin_hash
        assert pd["transitions_total"] == 2
        assert len(pd["transitions"]) == 2
        # Check transition details
        t1 = pd["transitions"][0]
        assert t1["agent"] == "test-agent"
        assert t1["agent_owner"] == "test-org"
        assert t1["agent_verified"] is True
        assert t1["reason"] == "Section 1 revised"
        assert t1["state_before"]  # hash present
        assert t1["state_after"]  # hash present

    def test_receipt_human_readable(self, agent, artifact):
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"edited",
            agent_id=agent.id,
            reason="Legal review",
        )
        r = provenance.receipt(artifact.id)
        hr = r["human_readable"]
        assert isinstance(hr, str)
        assert "pruv.provenance receipt" in hr
        assert "test-document" in hr
        assert "Document" in hr  # classification capitalized
        assert "test-org" in hr
        assert "test-agent" in hr
        assert "Legal review" in hr
        assert "Verified by pruv" in hr

    def test_receipt_with_unauthorized(self, artifact):
        expired = identity.register(
            name="bad-agent",
            framework="custom",
            owner="unknown-org",
            scope=["none"],
            purpose="Testing",
            valid_from="2020-01-01",
            valid_until="2020-12-31",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"suspicious edit",
            agent_id=expired.id,
            reason="Unauthorized change",
        )
        r = provenance.receipt(artifact.id)
        pd = r["product_data"]
        assert len(pd["unauthorized_transitions"]) == 1
        assert pd["unauthorized_transitions"][0]["agent"] == "bad-agent"
        hr = r["human_readable"]
        assert "Unauthorized transitions detected" in hr

    def test_receipt_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            provenance.receipt("nonexistent-id")


# ─── 9. Cross-product: receipt pulls identity chains ─────────────────────────


class TestCrossProductReceiptPullsIdentity:
    def test_receipt_resolves_agent_identity(self, artifact):
        agent_a = identity.register(
            name="drafting-agent",
            framework="crewai",
            owner="legal-team",
            scope=["document.edit"],
            purpose="Drafting",
            valid_until="2099-12-31",
        )
        agent_b = identity.register(
            name="review-agent",
            framework="langchain",
            owner="legal-team",
            scope=["document.review"],
            purpose="Review",
            valid_until="2099-12-31",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"drafted",
            agent_id=agent_a.id,
            reason="Initial draft",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"reviewed",
            agent_id=agent_b.id,
            reason="Legal review complete",
        )
        r = provenance.receipt(artifact.id)
        pd = r["product_data"]
        assert pd["transitions"][0]["agent"] == "drafting-agent"
        assert pd["transitions"][0]["agent_owner"] == "legal-team"
        assert pd["transitions"][1]["agent"] == "review-agent"
        assert pd["transitions"][1]["agent_owner"] == "legal-team"

        hr = r["human_readable"]
        assert "drafting-agent" in hr
        assert "review-agent" in hr
        assert "legal-team" in hr


# ─── 10. Cross-product: broken identity chain flags provenance ───────────────


class TestCrossProductBrokenIdentity:
    def test_broken_identity_flags_provenance_transition(self, artifact):
        agent = identity.register(
            name="tampered-agent",
            framework="custom",
            owner="test-org",
            scope=["document.edit"],
            purpose="Testing",
            valid_until="2099-12-31",
        )
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"edit by soon-tampered agent",
            agent_id=agent.id,
            reason="Edit before tampering",
        )
        # Tamper with the agent's identity chain
        id_registry = identity._get_registry()
        with sqlite3.connect(id_registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM identities WHERE id = ?",
                (agent.id,),
            ).fetchone()
            chain_data = json.loads(row[0])
            chain_data["entries"][0]["y"] = "tampered_identity"
            conn.execute(
                "UPDATE identities SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), agent.id),
            )
        # Now verify provenance — should flag this transition
        result = provenance.verify(artifact.id)
        assert result.intact is True  # provenance chain itself is fine
        assert len(result.unauthorized_transitions) == 1
        assert result.unauthorized_transitions[0].agent_name == "tampered-agent"


# ─── 11. Cross-product: revoked agent unauthorized in provenance ─────────────


class TestCrossProductRevokedAgent:
    def test_revoked_agent_unauthorized_even_if_hash_intact(self, artifact):
        agent = identity.register(
            name="revoked-agent",
            framework="custom",
            owner="test-org",
            scope=["document.edit"],
            purpose="Testing",
            valid_until="2099-12-31",
        )
        # Transition while agent is active
        provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"pre-revocation edit",
            agent_id=agent.id,
            reason="Before revocation",
        )
        # Revoke the agent
        identity.revoke(agent.id, reason="Trust broken")
        # Verify provenance — transition should now be flagged
        # because verify re-checks agent status at query time
        result = provenance.verify(artifact.id)
        assert result.intact is True  # provenance chain hashes are fine
        assert len(result.unauthorized_transitions) == 1
        unauth = result.unauthorized_transitions[0]
        assert unauth.agent_name == "revoked-agent"
        assert unauth.agent_in_scope is False

        # Receipt should reflect this
        r = provenance.receipt(artifact.id)
        pd = r["product_data"]
        assert len(pd["unauthorized_transitions"]) == 1


# ─── Edge cases ──────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_transition_nonexistent_artifact_raises(self, agent):
        with pytest.raises(ValueError, match="not found"):
            provenance.transition(
                artifact_id="does-not-exist",
                updated_content=b"content",
                agent_id=agent.id,
                reason="test",
            )

    def test_transition_nonexistent_agent_still_recorded(self, artifact):
        """Transition with unknown agent is recorded but marked unauthorized."""
        t = provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"modified",
            agent_id="fake-agent-id",
            reason="Unknown agent edit",
        )
        assert t.agent_in_scope is False
        assert t.agent_name == "unknown"

        result = provenance.verify(artifact.id)
        assert len(result.unauthorized_transitions) == 1

    def test_multiple_artifacts_isolated(self, agent):
        art_a = provenance.origin(
            content=b"doc A",
            name="artifact-a",
            classification="document",
            owner="org-a",
        )
        art_b = provenance.origin(
            content=b"doc B",
            name="artifact-b",
            classification="code",
            owner="org-b",
        )
        provenance.transition(
            artifact_id=art_a.id,
            updated_content=b"A modified",
            agent_id=agent.id,
            reason="Edit A",
        )
        result_a = provenance.verify(art_a.id)
        result_b = provenance.verify(art_b.id)
        assert result_a.entries == 2
        assert result_b.entries == 1
        assert result_a.intact is True
        assert result_b.intact is True

    def test_transition_with_metadata(self, agent, artifact):
        t = provenance.transition(
            artifact_id=artifact.id,
            updated_content=b"with meta",
            agent_id=agent.id,
            reason="Metadata test",
            metadata={"diff_lines": 42, "tool": "sed"},
        )
        assert t.metadata == {"diff_lines": 42, "tool": "sed"}
