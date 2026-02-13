"""Tests for xycore — the XY primitive."""

import json
import tempfile
import time
from pathlib import Path

from xycore import (
    LocalStorage,
    ThinkingPhase,
    XYChain,
    XYEntry,
    XYReceipt,
    compute_xy,
    hash_state,
    redact_state,
    verify_chain,
    verify_entry,
)


class TestHashState:
    def test_deterministic(self):
        state = {"b": 2, "a": 1}
        h1 = hash_state(state)
        h2 = hash_state({"a": 1, "b": 2})
        assert h1 == h2

    def test_different_states_different_hashes(self):
        h1 = hash_state({"a": 1})
        h2 = hash_state({"a": 2})
        assert h1 != h2

    def test_empty_state(self):
        h = hash_state({})
        assert isinstance(h, str)
        assert len(h) == 64


class TestComputeXY:
    def test_format(self):
        xy = compute_xy("abc", "deploy", "def", 1234567890.0)
        assert xy.startswith("xy_")
        assert len(xy) == 67  # xy_ + 64 hex chars

    def test_deterministic(self):
        xy1 = compute_xy("a", "op", "b", 1.0)
        xy2 = compute_xy("a", "op", "b", 1.0)
        assert xy1 == xy2

    def test_different_inputs(self):
        xy1 = compute_xy("a", "op1", "b", 1.0)
        xy2 = compute_xy("a", "op2", "b", 1.0)
        assert xy1 != xy2


class TestXYEntry:
    def test_create(self):
        entry = XYEntry.create(
            index=0,
            operation="test",
            x="GENESIS",
            y=hash_state({"done": True}),
            x_state=None,
            y_state={"done": True},
            timestamp=1000.0,
        )
        assert entry.index == 0
        assert entry.x == "GENESIS"
        assert entry.xy.startswith("xy_")
        assert entry.status == "success"
        assert entry.verified is True

    def test_serialization(self):
        entry = XYEntry.create(
            index=0, operation="test", x="GENESIS",
            y=hash_state({}), timestamp=1000.0,
        )
        d = entry.to_dict()
        restored = XYEntry.from_dict(d)
        assert restored.index == entry.index
        assert restored.xy == entry.xy
        assert restored.x == entry.x
        assert restored.y == entry.y

    def test_verify_entry(self):
        entry = XYEntry.create(
            index=0, operation="test", x="GENESIS",
            y=hash_state({}), timestamp=1000.0,
        )
        assert verify_entry(entry)

    def test_tampered_entry_fails(self):
        entry = XYEntry.create(
            index=0, operation="test", x="GENESIS",
            y=hash_state({}), timestamp=1000.0,
        )
        entry.y = "tampered"
        assert not verify_entry(entry)


class TestXYChain:
    def test_empty_chain(self):
        chain = XYChain(name="test")
        assert chain.length == 0
        assert chain.head == "GENESIS"
        assert chain.root is None

    def test_append(self):
        chain = XYChain(name="test")
        entry = chain.append("op1", y_state={"step": 1})
        assert entry.index == 0
        assert entry.x == "GENESIS"
        assert chain.length == 1

    def test_chain_linking(self):
        chain = XYChain(name="test")
        e0 = chain.append("op1", y_state={"step": 1})
        e1 = chain.append("op2", y_state={"step": 2})
        assert e1.x == e0.y

    def test_verify_valid_chain(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"step": 1})
        chain.append("op2", y_state={"step": 2})
        chain.append("op3", y_state={"step": 3})
        valid, break_idx = chain.verify()
        assert valid
        assert break_idx is None

    def test_verify_tampered_chain(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"step": 1})
        chain.append("op2", y_state={"step": 2})
        chain.entries[0].y = "tampered"
        valid, break_idx = chain.verify()
        assert not valid

    def test_serialization(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"step": 1})
        chain.append("op2", y_state={"step": 2})
        d = chain.to_dict()
        restored = XYChain.from_dict(d)
        assert restored.length == 2
        assert restored.name == "test"
        valid, _ = restored.verify()
        assert valid

    def test_auto_redact(self):
        chain = XYChain(name="test", auto_redact=True)
        chain.append("op", y_state={"password": "secret123"})
        assert chain.entries[0].y_state["password"] == "[REDACTED]"

    def test_len_and_getitem(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"a": 1})
        chain.append("op2", y_state={"b": 2})
        assert len(chain) == 2
        assert chain[0].operation == "op1"
        assert chain[1].operation == "op2"


class TestVerifyChain:
    def test_empty_chain(self):
        valid, idx = verify_chain([])
        assert valid
        assert idx is None

    def test_single_entry(self):
        entry = XYEntry.create(
            index=0, operation="init", x="GENESIS",
            y=hash_state({"init": True}), timestamp=1000.0,
        )
        valid, idx = verify_chain([entry])
        assert valid

    def test_broken_genesis(self):
        entry = XYEntry.create(
            index=0, operation="init", x="NOT_GENESIS",
            y=hash_state({"init": True}), timestamp=1000.0,
        )
        valid, idx = verify_chain([entry])
        assert not valid
        assert idx == 0


class TestXYReceipt:
    def test_receipt_hash(self):
        receipt = XYReceipt(
            id="r1", task="test", started=1000.0, completed=1001.0,
            duration=1.0, chain_id="c1", entry_count=3,
            first_x="GENESIS", final_y="abc", root_xy="xy_123",
            head_xy="xy_456", all_verified=True,
        )
        h = receipt.hash
        assert isinstance(h, str)
        assert len(h) == 64

    def test_receipt_serialization(self):
        receipt = XYReceipt(
            id="r1", task="test", started=1000.0, completed=1001.0,
            duration=1.0, chain_id="c1", entry_count=3,
            first_x="GENESIS", final_y="abc", root_xy="xy_123",
            head_xy="xy_456", all_verified=True,
            thinking=ThinkingPhase(prompt="test", reasoning="because"),
        )
        d = receipt.to_dict()
        restored = XYReceipt.from_dict(d)
        assert restored.id == "r1"
        assert restored.thinking is not None
        assert restored.thinking.prompt == "test"
        assert restored.hash == receipt.hash


class TestRedactState:
    def test_redact_password(self):
        state = {"username": "admin", "password": "secret123"}
        redacted = redact_state(state)
        assert redacted["username"] == "admin"
        assert redacted["password"] == "[REDACTED]"

    def test_redact_api_key(self):
        state = {"api_key": "my-key", "data": "safe"}
        redacted = redact_state(state)
        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["data"] == "safe"

    def test_redact_stripe_key_in_value(self):
        state = {"config": "key is sk_live_abc123xyz"}
        redacted = redact_state(state)
        assert "sk_live_" not in redacted["config"]

    def test_redact_github_token(self):
        state = {"note": "token ghp_abc123xyz456"}
        redacted = redact_state(state)
        assert "ghp_" not in redacted["note"]

    def test_redact_aws_key(self):
        state = {"key": "AKIAIOSFODNN7EXAMPLE"}
        redacted = redact_state(state)
        assert "AKIA" not in redacted["key"]

    def test_redact_nested(self):
        state = {"outer": {"inner": {"password": "secret"}}}
        redacted = redact_state(state)
        assert redacted["outer"]["inner"]["password"] == "[REDACTED]"

    def test_redact_pruv_keys(self):
        state = {"note": "key pv_live_abc123"}
        redacted = redact_state(state)
        assert "pv_live_" not in redacted["note"]


class TestLocalStorage:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(tmpdir)
            chain = XYChain(name="test")
            chain.append("op1", y_state={"step": 1})
            storage.save(chain)
            loaded = storage.load(chain.id)
            assert loaded.length == 1
            assert loaded.name == "test"

    def test_list_chains(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(tmpdir)
            c1 = XYChain(name="first")
            c2 = XYChain(name="second")
            storage.save(c1)
            storage.save(c2)
            chains = storage.list_chains()
            assert len(chains) == 2

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(tmpdir)
            chain = XYChain(name="test")
            storage.save(chain)
            assert storage.exists(chain.id)
            storage.delete(chain.id)
            assert not storage.exists(chain.id)

    def test_load_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(tmpdir)
            try:
                storage.load("nonexistent")
                assert False, "Should have raised FileNotFoundError"
            except FileNotFoundError:
                pass
