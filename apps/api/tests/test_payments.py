"""Tests for payment verification endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import generate_api_key
from app.main import app

client = TestClient(app)

TEST_KEY = generate_api_key("pv_test_")
AUTH_HEADER = {"Authorization": f"Bearer {TEST_KEY}"}


def _create_chain(name: str = "payment-test") -> str:
    resp = client.post("/v1/chains", json={"name": name}, headers=AUTH_HEADER)
    return resp.json()["id"]


def _append_entry(
    chain_id: str,
    operation: str = "transfer",
    y_state: dict | None = None,
    metadata: dict | None = None,
) -> dict:
    resp = client.post(
        f"/v1/chains/{chain_id}/entries",
        json={
            "operation": operation,
            "y_state": y_state or {"v": 1},
            "metadata": metadata or {},
        },
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 200
    return resp.json()


def _make_xy_proof(
    sender: str = "alice",
    recipient: str = "bob",
    amount: float = 250.0,
    sender_balance: float = 1000.0,
    recipient_balance: float = 500.0,
) -> dict:
    """Create a valid xy_proof dict using BalanceProof."""
    from xycore.balance import BalanceProof

    proof = BalanceProof.transfer(
        balances={sender: sender_balance, recipient: recipient_balance},
        sender=sender,
        recipient=recipient,
        amount=amount,
    )
    return proof.to_dict()


class TestEntryWithXYProof:
    def test_entry_stores_xy_proof_in_metadata(self):
        chain_id = _create_chain()
        xy_proof = _make_xy_proof()

        entry = _append_entry(
            chain_id,
            operation="payment.transfer",
            y_state={"alice": 750.0, "bob": 750.0},
            metadata={"xy_proof": xy_proof},
        )

        assert "xy_proof" in entry["metadata"]
        assert entry["metadata"]["xy_proof"]["xy"].startswith("xy_")
        assert entry["metadata"]["xy_proof"]["valid"] is True

    def test_entry_xy_proof_returned_on_get(self):
        chain_id = _create_chain()
        xy_proof = _make_xy_proof()

        _append_entry(
            chain_id,
            operation="payment.transfer",
            metadata={"xy_proof": xy_proof},
        )

        resp = client.get(f"/v1/chains/{chain_id}/entries", headers=AUTH_HEADER)
        assert resp.status_code == 200
        entries = resp.json()["entries"]
        assert len(entries) == 1
        assert "xy_proof" in entries[0]["metadata"]


class TestVerifyPayments:
    def test_verify_payments_all_valid(self):
        chain_id = _create_chain("verify-payments-valid")

        # Add two payment entries with valid proofs
        proof1 = _make_xy_proof("alice", "bob", 100.0, 1000.0, 500.0)
        _append_entry(chain_id, "payment.transfer", metadata={"xy_proof": proof1})

        proof2 = _make_xy_proof("bob", "charlie", 50.0, 600.0, 200.0)
        _append_entry(chain_id, "payment.transfer", metadata={"xy_proof": proof2})

        resp = client.get(
            f"/v1/chains/{chain_id}/verify-payments", headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["all_valid"] is True
        assert data["payment_count"] == 2
        assert data["verified_count"] == 2
        assert data["breaks"] == []
        assert data["total_volume"] == 150.0
        assert "✓" in data["message"]

    def test_verify_payments_empty_chain(self):
        chain_id = _create_chain("verify-payments-empty")

        resp = client.get(
            f"/v1/chains/{chain_id}/verify-payments", headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_count"] == 0
        assert data["all_valid"] is False
        assert data["total_volume"] == 0.0

    def test_verify_payments_no_payment_entries(self):
        chain_id = _create_chain("verify-payments-no-payments")
        _append_entry(chain_id, "deploy", y_state={"version": "1.0"})
        _append_entry(chain_id, "test", y_state={"passed": True})

        resp = client.get(
            f"/v1/chains/{chain_id}/verify-payments", headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_count"] == 0
        assert data["message"] == "No payment entries found"

    def test_verify_payments_mixed_entries(self):
        chain_id = _create_chain("verify-payments-mixed")

        # Non-payment entry
        _append_entry(chain_id, "deploy", y_state={"version": "1.0"})

        # Payment entry
        proof = _make_xy_proof("alice", "bob", 250.0, 1000.0, 500.0)
        _append_entry(chain_id, "payment.transfer", metadata={"xy_proof": proof})

        # Another non-payment entry
        _append_entry(chain_id, "test", y_state={"status": "pass"})

        resp = client.get(
            f"/v1/chains/{chain_id}/verify-payments", headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_count"] == 1
        assert data["verified_count"] == 1
        assert data["all_valid"] is True

    def test_verify_payments_tampered_proof(self):
        chain_id = _create_chain("verify-payments-tampered")

        proof = _make_xy_proof("alice", "bob", 250.0, 1000.0, 500.0)
        # Tamper: change the after balance
        proof["after"]["alice"] = 900.0

        _append_entry(chain_id, "payment.transfer", metadata={"xy_proof": proof})

        resp = client.get(
            f"/v1/chains/{chain_id}/verify-payments", headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["all_valid"] is False
        assert data["payment_count"] == 1
        assert data["verified_count"] == 0
        assert len(data["breaks"]) == 1
        assert "✗" in data["message"]

    def test_verify_payments_final_balances(self):
        chain_id = _create_chain("verify-payments-balances")

        proof = _make_xy_proof("alice", "bob", 250.0, 1000.0, 500.0)
        _append_entry(chain_id, "payment.transfer", metadata={"xy_proof": proof})

        resp = client.get(
            f"/v1/chains/{chain_id}/verify-payments", headers=AUTH_HEADER,
        )
        data = resp.json()
        assert data["final_balances"]["alice"] == 750.0
        assert data["final_balances"]["bob"] == 750.0

    def test_verify_payments_chain_not_found(self):
        resp = client.get(
            "/v1/chains/nonexistent/verify-payments", headers=AUTH_HEADER,
        )
        assert resp.status_code == 404

    def test_verify_payments_requires_auth(self):
        resp = client.get("/v1/chains/some-id/verify-payments")
        assert resp.status_code == 401

    def test_verify_payments_nested_data_path(self):
        """xy_proof nested under metadata.data (Agent path)."""
        chain_id = _create_chain("verify-payments-nested")

        proof = _make_xy_proof("alice", "bob", 100.0, 1000.0, 500.0)
        _append_entry(
            chain_id,
            "payment.transfer",
            metadata={
                "data": {
                    "sender": "alice",
                    "recipient": "bob",
                    "amount": 100.0,
                    "xy_proof": proof,
                },
            },
        )

        resp = client.get(
            f"/v1/chains/{chain_id}/verify-payments", headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_count"] == 1
        assert data["verified_count"] == 1
        assert data["all_valid"] is True
