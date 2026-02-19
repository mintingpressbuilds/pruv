"""Tests for pruv.identity — the new implementation with scope, owner, purpose,
validity period, revocation, and human-readable receipts.

Test cases from the spec:
1. Register agent — chain has exactly one entry, X is null
2. Act in scope — in_scope is True on entry
3. Act out of scope — in_scope is False, action still recorded
4. Verify intact chain — returns all counts correct
5. Verify broken chain — returns break_at with correct entry index
6. Verify expired identity — active is False
7. Revoke identity — status updates, chain appends correctly
8. Receipt format — all fields present, human readable string generated
"""

import os
import tempfile

import pytest

from pruv.identity import (
    AgentIdentity,
    IdentityAction,
    VerificationResult,
    register,
    act,
    verify,
    receipt,
    revoke,
    configure,
    _reset,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Each test gets its own SQLite database."""
    db_path = str(tmp_path / "test_identity.db")
    configure(db_path=db_path)
    yield db_path
    _reset()


@pytest.fixture
def agent():
    """Register a default test agent."""
    return register(
        name="test-agent",
        framework="custom",
        owner="test-org",
        scope=["file.read", "file.write", "deploy.staging"],
        purpose="Automated testing",
        valid_until="2099-12-31",
    )


# ─── 1. Register agent ──────────────────────────────────────────────────────


class TestRegister:
    def test_register_returns_agent_identity(self):
        agent = register(
            name="deployment-agent",
            framework="crewai",
            owner="acme-corp",
            scope=["file.read", "file.write", "deploy.production"],
            purpose="Automated production deployments",
            valid_until="2099-12-31",
        )
        assert isinstance(agent, AgentIdentity)
        assert agent.name == "deployment-agent"
        assert agent.framework == "crewai"
        assert agent.owner == "acme-corp"
        assert agent.scope == ["file.read", "file.write", "deploy.production"]
        assert agent.purpose == "Automated production deployments"
        assert agent.status == "active"
        assert agent.id  # uuid present
        assert agent.chain_id  # chain id present
        assert agent.created_at  # timestamp present
        assert agent.valid_from  # auto-set to now
        assert agent.valid_until == "2099-12-31"

    def test_register_chain_has_one_entry(self):
        agent = register(
            name="single-entry-test",
            framework="custom",
            owner="test-org",
            scope=["test.run"],
            purpose="Testing chain entry count",
            valid_until="2099-12-31",
        )
        result = verify(agent.id)
        assert result.entries == 1

    def test_register_first_entry_x_is_genesis(self):
        """First chain entry X state should be null (GENESIS in xycore)."""
        from pruv.identity.registry import IdentityRegistry

        agent = register(
            name="genesis-test",
            framework="custom",
            owner="test-org",
            scope=["test.run"],
            purpose="Testing genesis entry",
            valid_until="2099-12-31",
        )
        # Load chain to inspect entries
        from pruv.identity import _get_registry

        registry = _get_registry()
        loaded = registry.load(agent.id)
        assert loaded is not None
        _, chain = loaded
        entry = chain.entries[0]
        assert entry.x == "GENESIS"
        assert entry.x_state is None

    def test_register_y_state_contains_identity(self):
        agent = register(
            name="y-state-test",
            framework="langchain",
            owner="test-org",
            scope=["file.read"],
            purpose="Testing y_state",
            valid_until="2099-12-31",
        )
        from pruv.identity import _get_registry

        _, chain = _get_registry().load(agent.id)
        y_state = chain.entries[0].y_state
        assert y_state["name"] == "y-state-test"
        assert y_state["framework"] == "langchain"
        assert y_state["owner"] == "test-org"
        assert y_state["scope"] == ["file.read"]
        assert y_state["purpose"] == "Testing y_state"
        assert y_state["event"] == "registration"

    def test_register_with_custom_valid_from(self):
        agent = register(
            name="custom-dates",
            framework="custom",
            owner="test-org",
            scope=["test.run"],
            purpose="Testing custom validity",
            valid_from="2026-01-01",
            valid_until="2026-12-31",
        )
        assert agent.valid_from == "2026-01-01"
        assert agent.valid_until == "2026-12-31"

    def test_register_with_metadata(self):
        agent = register(
            name="metadata-agent",
            framework="custom",
            owner="test-org",
            scope=["test.run"],
            purpose="Testing metadata",
            valid_until="2099-12-31",
            metadata={"version": "1.0", "env": "test"},
        )
        from pruv.identity import _get_registry

        _, chain = _get_registry().load(agent.id)
        y_state = chain.entries[0].y_state
        assert y_state["metadata"] == {"version": "1.0", "env": "test"}


# ─── 2. Act in scope ────────────────────────────────────────────────────────


class TestActInScope:
    def test_act_in_scope_returns_identity_action(self, agent):
        action = act(
            agent_id=agent.id,
            action="read config.yml",
            action_scope="file.read",
        )
        assert isinstance(action, IdentityAction)
        assert action.agent_id == agent.id
        assert action.action == "read config.yml"
        assert action.action_scope == "file.read"
        assert action.in_scope is True
        assert action.entry_index == 1  # index 0 is registration

    def test_act_in_scope_verification(self, agent):
        act(agent_id=agent.id, action="read file", action_scope="file.read")
        result = verify(agent.id)
        assert result.in_scope_count == 1
        assert len(result.out_of_scope_actions) == 0

    def test_act_multiple_in_scope(self, agent):
        act(agent_id=agent.id, action="read file", action_scope="file.read")
        act(agent_id=agent.id, action="write file", action_scope="file.write")
        act(
            agent_id=agent.id,
            action="deploy to staging",
            action_scope="deploy.staging",
        )
        result = verify(agent.id)
        assert result.entries == 4  # 1 registration + 3 actions
        assert result.in_scope_count == 3


# ─── 3. Act out of scope ────────────────────────────────────────────────────


class TestActOutOfScope:
    def test_act_out_of_scope_still_recorded(self, agent):
        """Out-of-scope actions are recorded, not blocked."""
        action = act(
            agent_id=agent.id,
            action="accessed /etc/passwd",
            action_scope="system.admin",
        )
        assert action.in_scope is False
        assert action.entry_index == 1

    def test_act_out_of_scope_in_verification(self, agent):
        act(
            agent_id=agent.id,
            action="accessed /etc/passwd",
            action_scope="system.admin",
        )
        result = verify(agent.id)
        assert result.in_scope_count == 0
        assert len(result.out_of_scope_actions) == 1
        oos = result.out_of_scope_actions[0]
        assert oos.action == "accessed /etc/passwd"
        assert oos.action_scope == "system.admin"
        assert oos.in_scope is False

    def test_mixed_scope_actions(self, agent):
        act(agent_id=agent.id, action="read file", action_scope="file.read")
        act(
            agent_id=agent.id,
            action="delete database",
            action_scope="db.admin",
        )
        act(agent_id=agent.id, action="write file", action_scope="file.write")
        act(
            agent_id=agent.id,
            action="external API call",
            action_scope="network.external",
        )
        result = verify(agent.id)
        assert result.in_scope_count == 2
        assert len(result.out_of_scope_actions) == 2


# ─── 4. Verify intact chain ─────────────────────────────────────────────────


class TestVerifyIntact:
    def test_verify_new_agent(self, agent):
        result = verify(agent.id)
        assert isinstance(result, VerificationResult)
        assert result.intact is True
        assert result.entries == 1
        assert result.verified_count == 1
        assert result.break_at is None
        assert result.break_detail is None
        assert result.active is True

    def test_verify_after_actions(self, agent):
        for i in range(5):
            act(
                agent_id=agent.id,
                action=f"action {i}",
                action_scope="file.read",
            )
        result = verify(agent.id)
        assert result.intact is True
        assert result.entries == 6  # 1 reg + 5 actions
        assert result.verified_count == 6
        assert result.in_scope_count == 5
        assert result.break_at is None

    def test_verify_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            verify("nonexistent-id")


# ─── 5. Verify broken chain ─────────────────────────────────────────────────


class TestVerifyBroken:
    def test_tampered_chain_detected(self, agent):
        """Modify stored chain data to simulate tampering."""
        act(agent_id=agent.id, action="action 1", action_scope="file.read")
        act(agent_id=agent.id, action="action 2", action_scope="file.write")

        # Tamper with the chain in storage
        from pruv.identity import _get_registry
        import json
        import sqlite3

        registry = _get_registry()
        with sqlite3.connect(registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM identities WHERE id = ?", (agent.id,)
            ).fetchone()
            chain_data = json.loads(row[0])
            # Tamper with entry 1's y value
            chain_data["entries"][1]["y"] = "tampered_hash_value"
            conn.execute(
                "UPDATE identities SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), agent.id),
            )

        result = verify(agent.id)
        assert result.intact is False
        assert result.break_at is not None
        assert result.break_detail is not None
        assert "expected_x" in result.break_detail
        assert "found_x" in result.break_detail

    def test_break_at_reports_correct_index(self, agent):
        """Chain break should report the exact entry index."""
        for i in range(5):
            act(
                agent_id=agent.id,
                action=f"action {i}",
                action_scope="file.read",
            )

        # Tamper with entry 3
        from pruv.identity import _get_registry
        import json
        import sqlite3

        registry = _get_registry()
        with sqlite3.connect(registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM identities WHERE id = ?", (agent.id,)
            ).fetchone()
            chain_data = json.loads(row[0])
            # Tamper with entry 3's y — this breaks the link at entry 4
            chain_data["entries"][3]["y"] = "tampered_hash"
            conn.execute(
                "UPDATE identities SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), agent.id),
            )

        result = verify(agent.id)
        assert result.intact is False
        # xycore detects tamper at entry 3 itself (XY proof invalidated)
        assert result.break_at == 3
        assert result.verified_count == 3  # entries 0-2 verified


# ─── 6. Verify expired identity ─────────────────────────────────────────────


class TestVerifyExpired:
    def test_expired_identity_active_false(self):
        agent = register(
            name="expired-agent",
            framework="custom",
            owner="test-org",
            scope=["test.run"],
            purpose="Testing expiry",
            valid_from="2020-01-01",
            valid_until="2020-12-31",
        )
        result = verify(agent.id)
        assert result.active is False
        assert result.intact is True  # chain is still intact

    def test_future_identity_active_false(self):
        agent = register(
            name="future-agent",
            framework="custom",
            owner="test-org",
            scope=["test.run"],
            purpose="Testing future validity",
            valid_from="2099-01-01",
            valid_until="2099-12-31",
        )
        result = verify(agent.id)
        assert result.active is False

    def test_current_identity_active_true(self):
        agent = register(
            name="active-agent",
            framework="custom",
            owner="test-org",
            scope=["test.run"],
            purpose="Testing current validity",
            valid_from="2020-01-01",
            valid_until="2099-12-31",
        )
        result = verify(agent.id)
        assert result.active is True


# ─── 7. Revoke identity ─────────────────────────────────────────────────────


class TestRevoke:
    def test_revoke_updates_status(self, agent):
        revoked = revoke(agent.id, reason="Project concluded")
        assert revoked.status == "revoked"

    def test_revoke_appends_to_chain(self, agent):
        act(agent_id=agent.id, action="some action", action_scope="file.read")
        revoke(agent.id, reason="No longer needed")
        result = verify(agent.id)
        # 1 registration + 1 action + 1 revocation = 3
        assert result.entries == 3

    def test_revoke_chain_intact(self, agent):
        revoke(agent.id, reason="Testing revocation")
        result = verify(agent.id)
        assert result.intact is True

    def test_revoke_sets_active_false(self, agent):
        revoke(agent.id, reason="Testing")
        result = verify(agent.id)
        assert result.active is False

    def test_revoke_persists(self, agent):
        revoke(agent.id, reason="Permanent")
        # Re-verify from storage
        result = verify(agent.id)
        assert result.active is False

    def test_double_revoke_raises(self, agent):
        revoke(agent.id, reason="First revocation")
        with pytest.raises(ValueError, match="already revoked"):
            revoke(agent.id, reason="Second revocation")

    def test_revoke_y_state_contains_reason(self, agent):
        revoke(agent.id, reason="Project concluded")
        from pruv.identity import _get_registry

        _, chain = _get_registry().load(agent.id)
        last_entry = chain.entries[-1]
        assert last_entry.y_state["event"] == "revocation"
        assert last_entry.y_state["reason"] == "Project concluded"
        assert last_entry.y_state["status"] == "revoked"

    def test_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            revoke("nonexistent-id", reason="test")


# ─── 8. Receipt format ──────────────────────────────────────────────────────


class TestReceipt:
    def test_receipt_universal_schema(self, agent):
        act(agent_id=agent.id, action="read file", action_scope="file.read")
        r = receipt(agent.id)
        # Universal fields
        assert r["pruv_version"] == "1.0"
        assert r["type"] == "identity"
        assert r["chain_id"] == agent.chain_id
        assert r["chain_intact"] is True
        assert r["entries"] == 2
        assert r["verified"] == "2/2"
        assert r["X"]  # non-empty hash
        assert r["Y"]  # non-empty hash
        assert r["XY"]  # non-empty proof
        assert r["XY"].startswith("xy_")
        assert r["timestamp"]  # ISO 8601

    def test_receipt_product_data(self, agent):
        act(agent_id=agent.id, action="read file", action_scope="file.read")
        r = receipt(agent.id)
        pd = r["product_data"]
        assert pd["agent_name"] == "test-agent"
        assert pd["framework"] == "custom"
        assert pd["owner"] == "test-org"
        assert pd["purpose"] == "Automated testing"
        assert pd["scope"] == ["file.read", "file.write", "deploy.staging"]
        assert pd["status"] == "active"
        assert pd["actions_total"] == 1
        assert pd["actions_in_scope"] == 1
        assert pd["out_of_scope"] == []
        assert pd["first_seen"] == agent.created_at
        assert pd["chain_break"] is None

    def test_receipt_human_readable(self, agent):
        act(agent_id=agent.id, action="read file", action_scope="file.read")
        r = receipt(agent.id)
        hr = r["human_readable"]
        assert isinstance(hr, str)
        assert "pruv.identity receipt" in hr
        assert "test-agent" in hr
        assert "custom" in hr  # framework
        assert "test-org" in hr  # owner
        assert "Automated testing" in hr  # purpose
        assert "file.read" in hr
        assert "file.write" in hr
        assert "Verified by pruv" in hr

    def test_receipt_with_out_of_scope(self, agent):
        act(
            agent_id=agent.id,
            action="accessed secrets",
            action_scope="system.admin",
        )
        r = receipt(agent.id)
        pd = r["product_data"]
        assert len(pd["out_of_scope"]) == 1
        assert pd["out_of_scope"][0]["action"] == "accessed secrets"
        assert pd["out_of_scope"][0]["attempted_scope"] == "system.admin"
        hr = r["human_readable"]
        assert "Out-of-scope actions detected" in hr

    def test_receipt_with_broken_chain(self, agent):
        act(agent_id=agent.id, action="action 1", action_scope="file.read")

        # Tamper
        from pruv.identity import _get_registry
        import json
        import sqlite3

        registry = _get_registry()
        with sqlite3.connect(registry.db_path) as conn:
            row = conn.execute(
                "SELECT chain_data FROM identities WHERE id = ?", (agent.id,)
            ).fetchone()
            chain_data = json.loads(row[0])
            chain_data["entries"][0]["y"] = "tampered"
            conn.execute(
                "UPDATE identities SET chain_data = ? WHERE id = ?",
                (json.dumps(chain_data), agent.id),
            )

        r = receipt(agent.id)
        assert r["chain_intact"] is False
        pd = r["product_data"]
        assert pd["chain_break"] is not None
        hr = r["human_readable"]
        assert "Chain integrity failure" in hr

    def test_receipt_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            receipt("nonexistent-id")


# ─── Additional edge cases ──────────────────────────────────────────────────


class TestEdgeCases:
    def test_act_with_metadata(self, agent):
        action = act(
            agent_id=agent.id,
            action="deploy v1.2.3",
            action_scope="deploy.staging",
            metadata={"version": "1.2.3", "commit": "abc123"},
        )
        assert action.metadata == {"version": "1.2.3", "commit": "abc123"}

    def test_act_on_nonexistent_agent_raises(self):
        with pytest.raises(ValueError, match="not found"):
            act(
                agent_id="does-not-exist",
                action="test",
                action_scope="test",
            )

    def test_multiple_agents_isolated(self, isolated_db):
        agent_a = register(
            name="agent-a",
            framework="custom",
            owner="org-a",
            scope=["scope.a"],
            purpose="Agent A",
            valid_until="2099-12-31",
        )
        agent_b = register(
            name="agent-b",
            framework="custom",
            owner="org-b",
            scope=["scope.b"],
            purpose="Agent B",
            valid_until="2099-12-31",
        )
        act(agent_id=agent_a.id, action="a-action", action_scope="scope.a")
        act(agent_id=agent_b.id, action="b-action", action_scope="scope.b")

        result_a = verify(agent_a.id)
        result_b = verify(agent_b.id)
        assert result_a.entries == 2
        assert result_b.entries == 2
        assert result_a.intact is True
        assert result_b.intact is True

    def test_chain_ordering_maintained(self, agent):
        for i in range(10):
            act(
                agent_id=agent.id,
                action=f"action-{i}",
                action_scope="file.read",
            )
        from pruv.identity import _get_registry

        _, chain = _get_registry().load(agent.id)
        for i, entry in enumerate(chain.entries):
            assert entry.index == i

    def test_scope_module_directly(self):
        from pruv.identity.scope import check_scope

        assert check_scope("file.read", ["file.read", "file.write"]) is True
        assert check_scope("db.admin", ["file.read", "file.write"]) is False
        assert check_scope("", []) is False
