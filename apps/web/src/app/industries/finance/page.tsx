"use client";

import { IndustryPage } from "@/components/industry-page";

export default function FinanceIndustryPage() {
  return (
    <IndustryPage
      icon={
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
      }
      title="Financial Services"
      subtitle="Every transaction, trade, and account modification needs a tamper-proof audit trail. pruv provides cryptographic certainty for financial operations at any scale."
      problem={{
        title: "The audit trail problem",
        description:
          "Financial regulators demand complete, tamper-proof audit trails. Current solutions rely on database logs and application-level logging, which can be modified, are difficult to independently verify, and often fail to capture the complete picture of a transaction lifecycle.",
        points: [
          "Database transaction logs can be modified by privileged users",
          "SOX, PCI-DSS, and MiFID II require tamper-evident records",
          "Reconciliation across systems is manual and error-prone",
          "Trade execution records must be provably unaltered for regulatory review",
          "Account balance changes need verifiable before-and-after snapshots",
          "Cross-border transactions involve multiple systems with no unified audit trail",
        ],
      }}
      solution={{
        title: "Tamper-proof financial records.",
        description:
          "pruv captures the before and after state of every financial operation as a cryptographically signed, verifiable record. Balances, transactions, trades, and account modifications all become provable state transitions.",
        xLabel: "Account state before",
        yLabel: "Account state after",
        example:
          "Example: X = {balance: 10000.00, currency: \"USD\"} \u2192 Y = {balance: 9750.00, currency: \"USD\", debit: 250.00}",
      }}
      codeExample={{
        filename: "transaction.py",
        code: `from pruv import xy_wrap, checkpoint
from decimal import Decimal

@xy_wrap(
    chain="account_transactions",
    sign=True,  # Ed25519 signature
    redact=["card_number", "cvv"]  # Auto-redact PCI data
)
def process_payment(payment: dict) -> dict:
    # X = payment request + current account state

    account = db.get_account(payment["account_id"])
    checkpoint("account_snapshot", {
        "balance": str(account.balance),
        "currency": account.currency
    })

    # Validate and process
    amount = Decimal(payment["amount"])
    if account.balance < amount:
        raise InsufficientFunds(account.balance, amount)

    # Execute the transfer
    account.balance -= amount
    db.save(account)

    # Record the settlement
    settlement = gateway.charge(payment)
    checkpoint("settlement", settlement)

    return {
        "transaction_id": settlement.id,
        "new_balance": str(account.balance),
        "amount_charged": str(amount),
        "status": "completed"
    }
    # Y = completed transaction with new balance
    # XY = signed, redacted proof of the transaction`,
      }}
      useCases={[
        {
          title: "Transaction audit trails",
          description:
            "Every financial transaction produces a verifiable record that regulators can independently validate. The complete lifecycle from initiation to settlement is captured as a chain of XY proofs that cannot be altered after the fact.",
        },
        {
          title: "Trade execution verification",
          description:
            "Prove that trades were executed at the stated price, time, and quantity. MiFID II transaction reporting becomes straightforward when every trade is a cryptographically signed state transition with verifiable timestamps.",
        },
        {
          title: "Account reconciliation",
          description:
            "Reconcile balances across systems with mathematical certainty. When every account change is an XY record, discrepancies become immediately visible by verifying the hash chain rather than comparing logs line by line.",
        },
        {
          title: "SOX compliance",
          description:
            "Meet Sarbanes-Oxley requirements for financial record integrity with cryptographic proof instead of process controls. Auditors can independently verify that records have not been tampered with.",
        },
        {
          title: "Fraud detection",
          description:
            "When every state transition is verifiable, detecting unauthorized modifications becomes deterministic. If a balance changed without a corresponding verified transaction, the break in the hash chain is immediate proof of tampering.",
        },
        {
          title: "Cross-border settlement",
          description:
            "Track funds across jurisdictions and systems with a unified chain of verifiable records. Each handoff between systems becomes an XY transition, creating an end-to-end audit trail that all parties can verify.",
        },
      ]}
    />
  );
}
