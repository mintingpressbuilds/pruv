"""Tests for PaymentChain — payment verification through pruv."""

from unittest.mock import MagicMock, patch

import pytest

from xycore.balance import BalanceProof
from pruv.payment import PaymentChain, PaymentReceipt, PaymentVerification


def _make_ledger(
    name: str = "test-ledger",
    initial_balances: dict | None = None,
) -> PaymentChain:
    """Create a PaymentChain with a mocked Agent (no network)."""
    with patch("pruv.payment.Agent") as MockAgent:
        mock_agent = MagicMock()
        mock_agent.action.return_value = {"id": "entry_1", "status": "ok"}
        mock_agent.verify.return_value = {"valid": True, "break_index": None}
        MockAgent.return_value = mock_agent

        ledger = PaymentChain(
            name=name,
            api_key="pv_test_mock",
            initial_balances=initial_balances,
        )
    # Replace the agent with our mock so subsequent calls work
    ledger.agent = mock_agent
    return ledger


class TestTransfer:
    def test_basic_transfer(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})
        receipt = ledger.transfer("alice", "bob", 250.0)

        assert isinstance(receipt, PaymentReceipt)
        assert receipt.amount == 250.0
        assert receipt.sender == "alice"
        assert receipt.recipient == "bob"
        assert receipt.xy_proof.valid
        assert receipt.xy_proof.balanced
        assert ledger.balance("alice") == 750.0
        assert ledger.balance("bob") == 750.0

    def test_transfer_with_source_and_reference(self):
        ledger = _make_ledger(initial_balances={"merchant": 5000.0})
        receipt = ledger.transfer(
            "merchant", "customer_1", 89.99,
            source="stripe", reference="pi_3abc123",
        )
        assert receipt.source == "stripe"
        assert receipt.reference == "pi_3abc123"

    def test_transfer_calls_agent_action(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})
        ledger.transfer("alice", "bob", 250.0, source="bank", memo="rent")

        ledger.agent.action.assert_called_once()
        call_kwargs = ledger.agent.action.call_args
        assert call_kwargs.kwargs["action_type"] == "payment.transfer"
        data = call_kwargs.kwargs["data"]
        assert data["sender"] == "alice"
        assert data["recipient"] == "bob"
        assert data["amount"] == 250.0
        assert data["source"] == "bank"
        assert data["memo"] == "rent"
        assert "xy_proof" in data
        assert BalanceProof.verify_proof(data["xy_proof"])

    def test_transfer_insufficient_balance(self):
        ledger = _make_ledger(initial_balances={"alice": 100.0, "bob": 500.0})
        with pytest.raises(ValueError, match="Insufficient balance"):
            ledger.transfer("alice", "bob", 200.0)

    def test_transfer_new_sender_starts_at_zero(self):
        ledger = _make_ledger()
        with pytest.raises(ValueError, match="Insufficient balance"):
            ledger.transfer("unknown", "bob", 10.0)

    def test_transfer_new_recipient(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0})
        receipt = ledger.transfer("alice", "new_user", 100.0)
        assert ledger.balance("new_user") == 100.0
        assert ledger.balance("alice") == 900.0
        assert receipt.xy_proof.valid

    def test_sequential_transfers(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})

        ledger.transfer("alice", "bob", 100.0)
        assert ledger.balance("alice") == 900.0
        assert ledger.balance("bob") == 600.0

        ledger.transfer("bob", "alice", 50.0)
        assert ledger.balance("alice") == 950.0
        assert ledger.balance("bob") == 550.0

        ledger.transfer("alice", "bob", 200.0)
        assert ledger.balance("alice") == 750.0
        assert ledger.balance("bob") == 750.0

        assert ledger.payment_count == 3
        assert ledger.total_volume == 350.0

    def test_transfer_tracks_proofs(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})
        ledger.transfer("alice", "bob", 100.0)
        ledger.transfer("bob", "alice", 50.0)
        assert len(ledger._proofs) == 2
        assert all(p.valid for p in ledger._proofs)
        assert all(p.balanced for p in ledger._proofs)


class TestDeposit:
    def test_deposit(self):
        ledger = _make_ledger()
        receipt = ledger.deposit("merchant", 10000.0, source="bank", reference="ACH-001")

        assert isinstance(receipt, dict)
        assert ledger.balance("merchant") == 10000.0

    def test_deposit_calls_agent_action(self):
        ledger = _make_ledger()
        ledger.deposit("merchant", 5000.0, source="bank")

        ledger.agent.action.assert_called_once()
        call_kwargs = ledger.agent.action.call_args
        assert call_kwargs.kwargs["action_type"] == "payment.deposit"
        data = call_kwargs.kwargs["data"]
        assert data["account"] == "merchant"
        assert data["amount"] == 5000.0
        assert data["balance_before"] == 0.0
        assert data["balance_after"] == 5000.0

    def test_deposit_adds_to_existing_balance(self):
        ledger = _make_ledger(initial_balances={"merchant": 1000.0})
        ledger.deposit("merchant", 500.0)
        assert ledger.balance("merchant") == 1500.0


class TestWithdraw:
    def test_withdraw(self):
        ledger = _make_ledger(initial_balances={"merchant": 10000.0})
        receipt = ledger.withdraw("merchant", 500.0, destination="bank_account")

        assert isinstance(receipt, dict)
        assert ledger.balance("merchant") == 9500.0

    def test_withdraw_insufficient_balance(self):
        ledger = _make_ledger(initial_balances={"merchant": 100.0})
        with pytest.raises(ValueError, match="Insufficient balance"):
            ledger.withdraw("merchant", 200.0)

    def test_withdraw_calls_agent_action(self):
        ledger = _make_ledger(initial_balances={"merchant": 5000.0})
        ledger.withdraw("merchant", 1000.0, destination="wire", reference="W-001")

        ledger.agent.action.assert_called_once()
        call_kwargs = ledger.agent.action.call_args
        assert call_kwargs.kwargs["action_type"] == "payment.withdraw"
        data = call_kwargs.kwargs["data"]
        assert data["account"] == "merchant"
        assert data["amount"] == 1000.0
        assert data["balance_before"] == 5000.0
        assert data["balance_after"] == 4000.0
        assert data["destination"] == "wire"


class TestBalance:
    def test_balance_known_account(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0})
        assert ledger.balance("alice") == 1000.0

    def test_balance_unknown_account(self):
        ledger = _make_ledger()
        assert ledger.balance("unknown") == 0.0


class TestVerifyPayments:
    def test_verify_all_valid(self):
        ledger = _make_ledger(initial_balances={
            "alice": 1000.0, "bob": 500.0, "charlie": 200.0,
        })
        ledger.transfer("alice", "bob", 100.0)
        ledger.transfer("bob", "charlie", 50.0)
        ledger.transfer("charlie", "alice", 25.0)

        result = ledger.verify_payments()
        assert isinstance(result, PaymentVerification)
        assert result.valid
        assert result.payment_count == 3
        assert result.total_volume == 175.0
        assert len(result.breaks) == 0
        assert "✓" in result.message

    def test_verify_calls_agent_verify(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})
        ledger.transfer("alice", "bob", 100.0)
        ledger.verify_payments()
        ledger.agent.verify.assert_called_once()

    def test_verify_no_payments(self):
        ledger = _make_ledger()
        result = ledger.verify_payments()
        assert result.valid
        assert result.payment_count == 0
        assert result.total_volume == 0.0

    def test_verify_detects_tampered_proof(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})
        ledger.transfer("alice", "bob", 100.0)
        ledger.transfer("alice", "bob", 200.0)

        # Tamper with first proof
        ledger._proofs[0].after["alice"] = 999.0

        result = ledger.verify_payments()
        assert not result.valid
        assert 0 in result.breaks
        assert "✗" in result.message

    def test_verify_final_balances(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})
        ledger.transfer("alice", "bob", 250.0)

        result = ledger.verify_payments()
        assert result.final_balances["alice"] == 750.0
        assert result.final_balances["bob"] == 750.0


class TestSummary:
    def test_summary(self):
        ledger = _make_ledger(initial_balances={"alice": 1000.0, "bob": 500.0})
        ledger.transfer("alice", "bob", 100.0)
        ledger.transfer("bob", "alice", 50.0)

        s = ledger.summary()
        assert s["name"] == "test-ledger"
        assert s["payment_count"] == 2
        assert s["total_volume"] == 150.0
        assert s["accounts"] == 2
        assert s["balances"]["alice"] == 950.0
        assert s["balances"]["bob"] == 550.0


class TestEndToEnd:
    def test_full_payment_flow(self):
        """Simulates the full flow from the integration spec."""
        ledger = _make_ledger()

        # Deposit funds
        ledger.deposit("merchant", 10000.0, source="bank", reference="ACH-001")
        assert ledger.balance("merchant") == 10000.0

        # Process payments
        ledger.transfer(
            "merchant", "customer_1", 250.0,
            source="stripe", reference="pi_001",
        )
        ledger.transfer(
            "merchant", "customer_2", 89.99,
            source="stripe", reference="pi_002",
        )
        ledger.transfer(
            "customer_1", "merchant", 50.0,
            source="stripe", reference="pi_003",
        )

        # Verify everything
        result = ledger.verify_payments()
        assert result.valid
        assert result.payment_count == 3
        assert result.total_volume == pytest.approx(389.99)

        # Check final balances
        assert ledger.balance("merchant") == pytest.approx(9710.01)
        assert ledger.balance("customer_1") == 200.0
        assert ledger.balance("customer_2") == 89.99

    def test_deposit_then_withdraw(self):
        ledger = _make_ledger()

        ledger.deposit("merchant", 5000.0, source="bank")
        assert ledger.balance("merchant") == 5000.0

        ledger.withdraw("merchant", 1000.0, destination="bank")
        assert ledger.balance("merchant") == 4000.0

    def test_multi_party_transfers(self):
        ledger = _make_ledger(initial_balances={
            "alice": 1000.0, "bob": 1000.0, "charlie": 1000.0,
        })

        ledger.transfer("alice", "bob", 100.0)
        ledger.transfer("bob", "charlie", 200.0)
        ledger.transfer("charlie", "alice", 300.0)

        assert ledger.balance("alice") == 1200.0
        assert ledger.balance("bob") == 900.0
        assert ledger.balance("charlie") == 900.0

        # Conservation: total is still 3000
        total = sum(ledger.balances.values())
        assert total == 3000.0

        result = ledger.verify_payments()
        assert result.valid
        assert result.payment_count == 3


class TestImports:
    def test_import_from_pruv(self):
        from pruv import PaymentChain, PaymentReceipt, PaymentVerification

        assert PaymentChain is not None
        assert PaymentReceipt is not None
        assert PaymentVerification is not None
