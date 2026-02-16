"""Tests for BalanceProof — cryptographic proof of balance state changes."""

import pytest

from xycore import XYChain
from xycore.balance import BalanceProof


class TestBasicTransfer:
    def test_transfer_creates_valid_proof(self):
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )
        assert proof.before == {"alice": 1000.0, "bob": 500.0}
        assert proof.after == {"alice": 750.0, "bob": 750.0}
        assert proof.valid
        assert proof.balanced
        assert proof.delta == {"alice": -250.0, "bob": 250.0}
        assert proof.x != proof.y
        assert proof.xy.startswith("xy_")

    def test_exact_balance_transfer(self):
        proof = BalanceProof.transfer(
            balances={"alice": 100.0, "bob": 0.0},
            sender="alice",
            recipient="bob",
            amount=100.0,
        )
        assert proof.after["alice"] == 0.0
        assert proof.after["bob"] == 100.0
        assert proof.valid
        assert proof.balanced

    def test_new_recipient(self):
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )
        assert proof.after["bob"] == 250.0
        assert proof.valid
        assert proof.balanced


class TestValidation:
    def test_insufficient_balance(self):
        with pytest.raises(ValueError, match="Insufficient balance"):
            BalanceProof.transfer(
                balances={"alice": 100.0, "bob": 500.0},
                sender="alice",
                recipient="bob",
                amount=200.0,
            )

    def test_negative_amount(self):
        with pytest.raises(ValueError, match="must be positive"):
            BalanceProof.transfer(
                balances={"alice": 1000.0, "bob": 500.0},
                sender="alice",
                recipient="bob",
                amount=-50.0,
            )

    def test_zero_amount(self):
        with pytest.raises(ValueError, match="must be positive"):
            BalanceProof.transfer(
                balances={"alice": 1000.0, "bob": 500.0},
                sender="alice",
                recipient="bob",
                amount=0.0,
            )

    def test_sender_not_found(self):
        with pytest.raises(KeyError):
            BalanceProof.transfer(
                balances={"alice": 1000.0},
                sender="charlie",
                recipient="bob",
                amount=100.0,
            )


class TestConservation:
    def test_conservation_of_value(self):
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )
        total_before = sum(proof.before.values())
        total_after = sum(proof.after.values())
        assert total_before == total_after

    def test_balanced_property(self):
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )
        assert proof.balanced


class TestSerialization:
    def test_roundtrip(self):
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
            memo="payment for design",
        )
        d = proof.to_dict()
        restored = BalanceProof.from_dict(d)
        assert restored.x == proof.x
        assert restored.y == proof.y
        assert restored.xy == proof.xy
        assert restored.valid
        assert restored.memo == "payment for design"

    def test_static_verify(self):
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )
        d = proof.to_dict()
        assert BalanceProof.verify_proof(d) is True

    def test_static_verify_detects_tampering(self):
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )
        d = proof.to_dict()
        d["after"]["alice"] = 900.0
        assert BalanceProof.verify_proof(d) is False


class TestDeterminism:
    def test_same_inputs_same_hashes(self):
        ts = 1739491200.0
        p1 = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
            timestamp=ts,
        )
        p2 = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
            timestamp=ts,
        )
        assert p1.x == p2.x
        assert p1.y == p2.y
        assert p1.xy == p2.xy


class TestChainIntegration:
    def test_balance_proof_works_with_xychain(self):
        chain = XYChain(name="payment-ledger")

        balances = {"alice": 1000.0, "bob": 500.0, "charlie": 200.0}

        # Transfer 1: alice -> bob
        p1 = BalanceProof.transfer(balances, "alice", "bob", 100.0)
        chain.append(
            operation="transfer",
            x_state=p1.before,
            y_state=p1.after,
            metadata={"xy_proof": p1.to_dict()},
        )
        balances["alice"] -= 100.0
        balances["bob"] += 100.0

        # Transfer 2: bob -> charlie
        p2 = BalanceProof.transfer(balances, "bob", "charlie", 50.0)
        chain.append(
            operation="transfer",
            x_state=p2.before,
            y_state=p2.after,
            metadata={"xy_proof": p2.to_dict()},
        )

        # Chain verifies
        valid, break_idx = chain.verify()
        assert valid
        assert break_idx is None

        # Chain rule holds: entry[1].x == entry[0].y
        assert chain.entries[1].x == chain.entries[0].y

    def test_xy_proof_stored_in_metadata(self):
        chain = XYChain(name="payment-ledger")
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0,
        )
        entry = chain.append(
            operation="transfer",
            y_state=proof.after,
            metadata={"xy_proof": proof.to_dict()},
        )
        assert "xy_proof" in entry.metadata
        assert entry.metadata["xy_proof"]["xy"] == proof.xy
        assert BalanceProof.verify_proof(entry.metadata["xy_proof"])
