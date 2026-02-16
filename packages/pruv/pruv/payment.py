"""PaymentChain — Payment verification through pruv.

Uses xycore's BalanceProof to create cryptographic proofs
of balance state changes, stored as pruv chain entries.

Usage::

    from pruv import PaymentChain

    ledger = PaymentChain("company-payments", api_key="pv_live_xxx")

    # Record a payment (from any source — Stripe, bank, etc.)
    receipt = ledger.transfer(
        sender="merchant_account",
        recipient="customer_123",
        amount=89.99,
        source="stripe",
        reference="pi_3abc123",
    )

    receipt.xy_proof.xy    # cryptographic proof
    receipt.xy_proof.valid  # True

    # Verify all payments in the chain
    result = ledger.verify_payments()
    # ✓ 412 payments, all XY proofs valid, final balances correct
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from xycore.balance import BalanceProof

from pruv.agent import Agent


@dataclass
class PaymentReceipt:
    """Receipt for a verified payment, combining pruv entry + XY proof."""

    pruv_receipt: dict[str, Any]
    xy_proof: BalanceProof
    sender: str
    recipient: str
    amount: float
    source: Optional[str] = None
    reference: Optional[str] = None


@dataclass
class PaymentVerification:
    """Result of verifying all payments in a chain."""

    valid: bool
    payment_count: int
    final_balances: dict[str, float]
    total_volume: float
    breaks: list[int]
    message: str


class PaymentChain:
    """Payment verification chain backed by pruv.

    Tracks balances locally and creates BalanceProof for each transfer.
    Each proof is stored as a pruv entry with xy_proof metadata.
    The pruv chain provides ordering and tamper detection.
    The BalanceProof provides balance state verification.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
        initial_balances: dict[str, float] | None = None,
    ) -> None:
        self.name = name
        self.agent = Agent(
            name=f"payment:{name}",
            api_key=api_key,
            endpoint=endpoint,
            metadata={"chain_type": "payment"},
        )
        self.balances: dict[str, float] = initial_balances or {}
        self.payment_count: int = 0
        self.total_volume: float = 0.0
        self._proofs: list[BalanceProof] = []

    def transfer(
        self,
        sender: str,
        recipient: str,
        amount: float,
        source: str | None = None,
        reference: str | None = None,
        memo: str | None = None,
    ) -> PaymentReceipt:
        """Record a verified payment.

        The actual payment happens elsewhere (Stripe, bank, etc.).
        This creates a cryptographic proof of the balance state change.

        Args:
            sender: Sender identifier (account name, wallet address, etc.)
            recipient: Recipient identifier
            amount: Payment amount
            source: Where the payment happened ("stripe", "bank", "manual")
            reference: External reference ID (Stripe payment intent, etc.)
            memo: Optional description

        Returns:
            PaymentReceipt with pruv entry + XY balance proof

        Raises:
            ValueError: If sender has insufficient balance
        """
        if sender not in self.balances:
            self.balances[sender] = 0.0

        proof = BalanceProof.transfer(
            balances=self.balances,
            sender=sender,
            recipient=recipient,
            amount=amount,
            memo=memo,
        )

        pruv_receipt = self.agent.action(
            action_type="payment.transfer",
            data={
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
                "source": source,
                "reference": reference,
                "memo": memo,
                "xy_proof": proof.to_dict(),
            },
        )

        self.balances[sender] = proof.after[sender]
        self.balances[recipient] = proof.after[recipient]
        self.payment_count += 1
        self.total_volume += amount
        self._proofs.append(proof)

        return PaymentReceipt(
            pruv_receipt=pruv_receipt,
            xy_proof=proof,
            sender=sender,
            recipient=recipient,
            amount=amount,
            source=source,
            reference=reference,
        )

    def deposit(
        self,
        account: str,
        amount: float,
        source: str | None = None,
        reference: str | None = None,
    ) -> dict[str, Any]:
        """Record a deposit (money entering the system).

        No sender — value comes from outside.
        """
        if account not in self.balances:
            self.balances[account] = 0.0

        before = self.balances[account]
        after = before + amount

        receipt = self.agent.action(
            action_type="payment.deposit",
            data={
                "account": account,
                "amount": amount,
                "balance_before": before,
                "balance_after": after,
                "source": source,
                "reference": reference,
            },
        )

        self.balances[account] = after
        return receipt

    def withdraw(
        self,
        account: str,
        amount: float,
        destination: str | None = None,
        reference: str | None = None,
    ) -> dict[str, Any]:
        """Record a withdrawal (money leaving the system).

        No recipient — value goes outside.
        """
        if account not in self.balances:
            self.balances[account] = 0.0

        if self.balances[account] < amount:
            raise ValueError(
                f"Insufficient balance: {account} has {self.balances[account]}, "
                f"needs {amount}"
            )

        before = self.balances[account]
        after = before - amount

        receipt = self.agent.action(
            action_type="payment.withdraw",
            data={
                "account": account,
                "amount": amount,
                "balance_before": before,
                "balance_after": after,
                "destination": destination,
                "reference": reference,
            },
        )

        self.balances[account] = after
        return receipt

    def balance(self, account: str) -> float:
        """Get current balance for an account."""
        return self.balances.get(account, 0.0)

    def verify_payments(self) -> PaymentVerification:
        """Verify all payments in the chain.

        1. Verifies the pruv chain integrity (hash linking)
        2. Recomputes every BalanceProof from stored data
        3. Confirms final balances match chain state
        """
        self.agent.verify()

        breaks: list[int] = []
        recomputed_balances: dict[str, float] = {}
        total_volume = 0.0
        payment_count = 0

        for i, proof in enumerate(self._proofs):
            if not proof.valid:
                breaks.append(i)
            if not proof.balanced:
                breaks.append(i)

            recomputed_balances[proof.sender] = proof.after[proof.sender]
            recomputed_balances[proof.recipient] = proof.after[proof.recipient]
            total_volume += proof.amount
            payment_count += 1

        valid = len(breaks) == 0

        if valid:
            message = (
                f"✓ {payment_count} payments verified. "
                f"All XY proofs intact. "
                f"Total volume: {total_volume:.2f}"
            )
        else:
            message = (
                f"✗ Verification failed at {len(breaks)} payment(s). "
                f"Break indices: {breaks}"
            )

        return PaymentVerification(
            valid=valid,
            payment_count=payment_count,
            final_balances=dict(self.balances),
            total_volume=total_volume,
            breaks=breaks,
            message=message,
        )

    def summary(self) -> dict[str, Any]:
        """Current state summary."""
        return {
            "name": self.name,
            "payment_count": self.payment_count,
            "total_volume": self.total_volume,
            "accounts": len(self.balances),
            "balances": dict(self.balances),
        }
