# XYCHAIN → PRUV Integration Build

## What This Is

This integrates xychain's payment verification math into the existing xycore + pruv stack. No new products. No new deployments. No nodes. No consensus. Just the XY balance proof model added to what already works.

After this build:

- xycore gains a `BalanceProof` class (the payment math)
- pruv gains a `PaymentChain` class (payment verification through existing API)
- pruv API gains optional `xy_proof` fields on entries
- pruv API gains a `/v1/chains/{id}/verify-payments` endpoint
- pruv dashboard gains payment markers in the chain timeline

**Read all existing code before writing anything.** Understand how xycore's `XYChain`, `XYEntry`, `hash_state`, and `compute_xy` work. Understand how pruv's `Agent` and `PruvClient` work. Then build.

-----

## Step 1: BalanceProof in xycore

Location: `packages/xycore/xycore/balance.py`

This is pure math. No network. No API. No database. Takes balances in, gives hashes out.

```python
# xycore/balance.py

"""
Balance proof — cryptographic proof of a balance state change.

A payment transforms balances. BalanceProof hashes both sides
and creates a cryptographic proof linking them.

    Before:  Alice=$1000, Bob=$500
    After:   Alice=$750,  Bob=$750

    X  = hash(before)
    Y  = hash(after)
    XY = hash(X + "transfer" + Y + timestamp)

The proof is verifiable by anyone with the before/after data.
The chain rule (Entry[N].x == Entry[N-1].y) ensures sequential integrity.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from xycore import hash_state, compute_xy


@dataclass
class BalanceProof:
    """
    Cryptographic proof of a balance state change.

    Usage:
        proof = BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=250.0
        )

        proof.x          # hash of balances before
        proof.y          # hash of balances after
        proof.xy         # cryptographic proof
        proof.valid      # True
        proof.before     # {"alice": 1000.0, "bob": 500.0}
        proof.after      # {"alice": 750.0, "bob": 750.0}
        proof.delta      # {"alice": -250.0, "bob": +250.0}
    """

    before: dict[str, float]            # Balances before transfer
    after: dict[str, float]             # Balances after transfer
    amount: float                       # Transfer amount
    sender: str                         # Sender identifier
    recipient: str                      # Recipient identifier
    timestamp: float = field(default_factory=time.time)
    memo: Optional[str] = None

    # Computed on init
    x: str = ""                         # Hash of before state
    y: str = ""                         # Hash of after state
    xy: str = ""                        # XY proof hash

    def __post_init__(self):
        self.x = hash_state(self._normalize(self.before))
        self.y = hash_state(self._normalize(self.after))
        self.xy = compute_xy(self.x, "transfer", self.y, self.timestamp)

    @classmethod
    def transfer(
        cls,
        balances: dict[str, float],
        sender: str,
        recipient: str,
        amount: float,
        memo: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> "BalanceProof":
        """
        Create a balance proof for a transfer.

        Args:
            balances: Current balances for all parties involved
            sender: Key in balances dict for sender
            recipient: Key in balances dict for recipient
            amount: Amount to transfer
            memo: Optional memo/reference
            timestamp: Optional timestamp (defaults to now)

        Raises:
            ValueError: If sender has insufficient balance
            KeyError: If sender or recipient not in balances
        """
        if sender not in balances:
            raise KeyError(f"Sender '{sender}' not found in balances")
        if recipient not in balances:
            # Recipient can be new — start at 0
            balances = {**balances, recipient: 0.0}

        if balances[sender] < amount:
            raise ValueError(
                f"Insufficient balance: {sender} has {balances[sender]}, "
                f"needs {amount}"
            )

        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")

        before = {sender: balances[sender], recipient: balances[recipient]}
        after = {
            sender: round(balances[sender] - amount, 8),
            recipient: round(balances[recipient] + amount, 8),
        }

        ts = timestamp or time.time()

        return cls(
            before=before,
            after=after,
            amount=amount,
            sender=sender,
            recipient=recipient,
            timestamp=ts,
            memo=memo,
        )

    @property
    def valid(self) -> bool:
        """Verify the proof by recomputing hashes."""
        expected_x = hash_state(self._normalize(self.before))
        expected_y = hash_state(self._normalize(self.after))
        expected_xy = compute_xy(expected_x, "transfer", expected_y, self.timestamp)
        return (
            self.x == expected_x
            and self.y == expected_y
            and self.xy == expected_xy
        )

    @property
    def delta(self) -> dict[str, float]:
        """Balance changes for each party."""
        return {
            party: round(self.after.get(party, 0) - self.before.get(party, 0), 8)
            for party in set(list(self.before.keys()) + list(self.after.keys()))
        }

    @property
    def balanced(self) -> bool:
        """Check that total in equals total out (conservation of value)."""
        return round(sum(self.delta.values()), 8) == 0.0

    def to_dict(self) -> dict:
        return {
            "before": self.before,
            "after": self.after,
            "amount": self.amount,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "memo": self.memo,
            "x": self.x,
            "y": self.y,
            "xy": self.xy,
            "valid": self.valid,
            "balanced": self.balanced,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BalanceProof":
        proof = cls(
            before=data["before"],
            after=data["after"],
            amount=data["amount"],
            sender=data["sender"],
            recipient=data["recipient"],
            timestamp=data["timestamp"],
            memo=data.get("memo"),
        )
        return proof

    @staticmethod
    def _normalize(balances: dict) -> dict:
        """Normalize balance dict for deterministic hashing."""
        return {k: str(round(v, 8)) for k, v in sorted(balances.items())}

    @staticmethod
    def verify_proof(proof_dict: dict) -> bool:
        """
        Verify a balance proof from its dict representation.
        Recomputes all hashes and checks they match.
        Anyone with the proof data can verify it.
        """
        proof = BalanceProof.from_dict(proof_dict)
        return proof.valid and proof.balanced
```

### Update xycore **init**.py

Add to existing exports:

```python
from xycore.balance import BalanceProof

__all__ = [
    # ... existing exports ...
    "BalanceProof",
]
```

### Tests for BalanceProof

Location: `packages/xycore/tests/test_balance_proof.py`

```python
# tests/test_balance_proof.py

from xycore.balance import BalanceProof
import pytest


def test_basic_transfer():
    proof = BalanceProof.transfer(
        balances={"alice": 1000.0, "bob": 500.0},
        sender="alice",
        recipient="bob",
        amount=250.0
    )
    assert proof.before == {"alice": 1000.0, "bob": 500.0}
    assert proof.after == {"alice": 750.0, "bob": 750.0}
    assert proof.valid
    assert proof.balanced
    assert proof.delta == {"alice": -250.0, "bob": 250.0}
    assert proof.x != proof.y
    assert proof.xy.startswith("xy_")


def test_insufficient_balance():
    with pytest.raises(ValueError, match="Insufficient balance"):
        BalanceProof.transfer(
            balances={"alice": 100.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=200.0
        )


def test_negative_amount():
    with pytest.raises(ValueError, match="must be positive"):
        BalanceProof.transfer(
            balances={"alice": 1000.0, "bob": 500.0},
            sender="alice",
            recipient="bob",
            amount=-50.0
        )


def test_new_recipient():
    proof = BalanceProof.transfer(
        balances={"alice": 1000.0},
        sender="alice",
        recipient="bob",
        amount=250.0
    )
    assert proof.after["bob"] == 250.0
    assert proof.valid
    assert proof.balanced


def test_sender_not_found():
    with pytest.raises(KeyError):
        BalanceProof.transfer(
            balances={"alice": 1000.0},
            sender="charlie",
            recipient="bob",
            amount=100.0
        )


def test_exact_balance_transfer():
    proof = BalanceProof.transfer(
        balances={"alice": 100.0, "bob": 0.0},
        sender="alice",
        recipient="bob",
        amount=100.0
    )
    assert proof.after["alice"] == 0.0
    assert proof.after["bob"] == 100.0
    assert proof.valid
    assert proof.balanced


def test_serialization_roundtrip():
    proof = BalanceProof.transfer(
        balances={"alice": 1000.0, "bob": 500.0},
        sender="alice",
        recipient="bob",
        amount=250.0,
        memo="payment for design"
    )
    d = proof.to_dict()
    restored = BalanceProof.from_dict(d)
    assert restored.x == proof.x
    assert restored.y == proof.y
    assert restored.xy == proof.xy
    assert restored.valid
    assert restored.memo == "payment for design"


def test_static_verify():
    proof = BalanceProof.transfer(
        balances={"alice": 1000.0, "bob": 500.0},
        sender="alice",
        recipient="bob",
        amount=250.0
    )
    d = proof.to_dict()
    assert BalanceProof.verify_proof(d) is True

    # Tamper with amount
    d["after"]["alice"] = 900.0
    assert BalanceProof.verify_proof(d) is False


def test_proof_deterministic():
    """Same inputs at same timestamp produce same hashes."""
    ts = 1739491200.0
    p1 = BalanceProof.transfer(
        balances={"alice": 1000.0, "bob": 500.0},
        sender="alice", recipient="bob", amount=250.0,
        timestamp=ts
    )
    p2 = BalanceProof.transfer(
        balances={"alice": 1000.0, "bob": 500.0},
        sender="alice", recipient="bob", amount=250.0,
        timestamp=ts
    )
    assert p1.x == p2.x
    assert p1.y == p2.y
    assert p1.xy == p2.xy


def test_conservation_of_value():
    """Total value in the system doesn't change."""
    proof = BalanceProof.transfer(
        balances={"alice": 1000.0, "bob": 500.0},
        sender="alice", recipient="bob", amount=250.0
    )
    total_before = sum(proof.before.values())
    total_after = sum(proof.after.values())
    assert total_before == total_after


def test_chain_integration():
    """BalanceProof works with XYChain."""
    from xycore import XYChain

    chain = XYChain(name="payment-ledger")

    balances = {"alice": 1000.0, "bob": 500.0, "charlie": 200.0}

    # Transfer 1: alice → bob
    p1 = BalanceProof.transfer(balances, "alice", "bob", 100.0)
    chain.append(
        operation="transfer",
        x_state=p1.before,
        y_state=p1.after,
        metadata={"xy_proof": p1.to_dict()}
    )
    balances["alice"] -= 100.0
    balances["bob"] += 100.0

    # Transfer 2: bob → charlie
    p2 = BalanceProof.transfer(balances, "bob", "charlie", 50.0)
    chain.append(
        operation="transfer",
        x_state=p2.before,
        y_state=p2.after,
        metadata={"xy_proof": p2.to_dict()}
    )

    # Chain verifies
    valid, break_idx = chain.verify()
    assert valid
    assert break_idx is None

    # Chain rule holds: entry[1].x == entry[0].y
    # This works because the y_state of transfer 1 (bob's new balance)
    # feeds into the x of transfer 2
    assert chain.entries[1].x == chain.entries[0].y
```

**Acceptance criteria for Step 1:**

- [ ] `from xycore import BalanceProof` works
- [ ] `BalanceProof.transfer()` creates valid proof
- [ ] `proof.valid` recomputes and verifies hashes
- [ ] `proof.balanced` confirms conservation of value
- [ ] Insufficient balance raises ValueError
- [ ] Negative amount raises ValueError
- [ ] New recipient (not in balances) starts at 0
- [ ] Serialization roundtrip preserves all data
- [ ] Static `verify_proof()` works on dict representation
- [ ] Same inputs + timestamp = same hashes (deterministic)
- [ ] BalanceProof integrates with existing XYChain
- [ ] All existing xycore tests still pass (nothing broken)

-----

## Step 2: PaymentChain in pruv

Location: `packages/pruv/pruv/payment.py`

This wraps the pruv Agent with balance-aware tracking and automatic XY proof creation. Uses xycore's BalanceProof under the hood.

```python
# pruv/payment.py

"""
PaymentChain — Payment verification through pruv.

Uses xycore's BalanceProof to create cryptographic proofs
of balance state changes, stored as pruv chain entries.

Usage:
    from pruv import PaymentChain

    ledger = PaymentChain("company-payments", api_key="pv_live_xxx")

    # Record a payment (from any source — Stripe, bank, etc.)
    receipt = ledger.transfer(
        sender="merchant_account",
        recipient="customer_123",
        amount=89.99,
        source="stripe",
        reference="pi_3abc123"
    )

    receipt.xy_proof.xy   # cryptographic proof
    receipt.xy_proof.valid # True

    # Verify all payments in the chain
    result = ledger.verify_payments()
    # ✓ 412 payments, all XY proofs valid, final balances correct
"""

from typing import Optional
from dataclasses import dataclass, field
from xycore.balance import BalanceProof
from pruv.agent import Agent


@dataclass
class PaymentReceipt:
    """Receipt for a verified payment, combining pruv entry + XY proof."""
    pruv_receipt: dict               # Standard pruv entry receipt
    xy_proof: BalanceProof           # XY balance proof
    sender: str
    recipient: str
    amount: float
    source: Optional[str] = None     # Where the actual payment happened
    reference: Optional[str] = None  # External reference (Stripe ID, etc.)


@dataclass
class PaymentVerification:
    """Result of verifying all payments in a chain."""
    valid: bool                      # All XY proofs intact
    payment_count: int               # Total payments verified
    final_balances: dict[str, float] # Current balances
    total_volume: float              # Sum of all transfer amounts
    breaks: list[int]                # Indices where verification failed
    message: str                     # Human-readable summary


class PaymentChain:
    """
    Payment verification chain backed by pruv.

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
        initial_balances: Optional[dict[str, float]] = None,
    ):
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
        source: Optional[str] = None,
        reference: Optional[str] = None,
        memo: Optional[str] = None,
    ) -> PaymentReceipt:
        """
        Record a verified payment.

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
        # Ensure sender exists in balances
        if sender not in self.balances:
            self.balances[sender] = 0.0

        # Create the XY balance proof
        proof = BalanceProof.transfer(
            balances=self.balances,
            sender=sender,
            recipient=recipient,
            amount=amount,
            memo=memo,
        )

        # Record as a pruv entry with xy_proof attached
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

        # Update local balances
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
        source: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> dict:
        """
        Record a deposit (money entering the system).
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
        destination: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> dict:
        """
        Record a withdrawal (money leaving the system).
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
        """
        Verify all payments in the chain.

        1. Verifies the pruv chain integrity (hash linking)
        2. Recomputes every BalanceProof from stored data
        3. Confirms final balances match chain state
        """
        # Verify pruv chain integrity
        chain_result = self.agent.verify()

        # Verify each XY proof
        breaks = []
        recomputed_balances: dict[str, float] = {}
        total_volume = 0.0
        payment_count = 0

        for i, proof in enumerate(self._proofs):
            if not proof.valid:
                breaks.append(i)
            if not proof.balanced:
                breaks.append(i)

            # Recompute balances
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

    def summary(self) -> dict:
        """Current state summary."""
        return {
            "name": self.name,
            "payment_count": self.payment_count,
            "total_volume": self.total_volume,
            "accounts": len(self.balances),
            "balances": dict(self.balances),
        }
```

### Update pruv **init**.py

Add to existing exports:

```python
from pruv.payment import PaymentChain, PaymentReceipt, PaymentVerification

__all__ = [
    # ... existing exports ...
    "PaymentChain",
    "PaymentReceipt",
    "PaymentVerification",
]
```

**Acceptance criteria for Step 2:**

- [ ] `from pruv import PaymentChain` works
- [ ] `ledger.transfer()` creates BalanceProof and stores via pruv Agent
- [ ] `ledger.deposit()` records money entering the system
- [ ] `ledger.withdraw()` records money leaving, rejects insufficient balance
- [ ] `ledger.balance()` returns current balance
- [ ] `ledger.verify_payments()` recomputes all proofs and reports result
- [ ] Each transfer creates a pruv entry with `xy_proof` in metadata
- [ ] Multiple sequential transfers maintain correct running balances
- [ ] PaymentReceipt contains both pruv receipt and BalanceProof
- [ ] All existing pruv tests still pass

-----

## Step 3: API Payment Endpoints

Location: `apps/api/app/routes/` — add to existing chain routes

### 3a: Accept xy_proof on entry creation

The existing entry creation endpoint should accept an optional `xy_proof` field in the data payload. No schema change needed — pruv entries already store arbitrary data as JSON. The `xy_proof` dict from BalanceProof.to_dict() goes into the entry's data field naturally.

Verify: submit an entry with `data.xy_proof` present. Confirm it's stored and returned on GET.

### 3b: Payment verification endpoint

```python
# Add to apps/api/app/routes/chains.py

@router.get("/v1/chains/{chain_id}/verify-payments")
async def verify_payments(chain_id: str, auth=Depends(require_auth)):
    """
    Verify all payment entries in a chain.

    Walks the chain, finds entries with xy_proof in data,
    recomputes each BalanceProof, verifies hashes match.

    Returns:
        - total payment entries found
        - number verified successfully
        - number with broken proofs
        - list of break indices
        - recomputed final balances
        - total volume
    """
    chain = await get_chain(chain_id)
    entries = await get_chain_entries(chain_id)

    payment_count = 0
    verified_count = 0
    breaks = []
    balances: dict[str, float] = {}
    total_volume = 0.0

    for i, entry in enumerate(entries):
        data = entry.get("data", {})

        # Skip non-payment entries
        if "xy_proof" not in data.get("data", {}):
            continue

        payment_count += 1
        xy_data = data["data"]["xy_proof"]

        # Recompute and verify the proof
        try:
            from xycore.balance import BalanceProof
            valid = BalanceProof.verify_proof(xy_data)

            if valid:
                verified_count += 1
                # Update running balances
                for party, bal in xy_data.get("after", {}).items():
                    balances[party] = bal
                total_volume += xy_data.get("amount", 0)
            else:
                breaks.append(i)
        except Exception as e:
            breaks.append(i)

    all_valid = len(breaks) == 0 and payment_count > 0

    return {
        "chain_id": chain_id,
        "payment_count": payment_count,
        "verified_count": verified_count,
        "breaks": breaks,
        "all_valid": all_valid,
        "final_balances": balances,
        "total_volume": total_volume,
        "message": (
            f"✓ {verified_count}/{payment_count} payments verified"
            if all_valid
            else f"✗ {len(breaks)} payment(s) failed verification"
        ),
    }
```

**Acceptance criteria for Step 3:**

- [ ] Entries with `xy_proof` in data are stored and returned correctly
- [ ] GET `/v1/chains/{id}/verify-payments` finds payment entries
- [ ] Recomputes each BalanceProof and verifies hashes
- [ ] Returns break indices for any failed verifications
- [ ] Returns recomputed final balances
- [ ] Returns total volume
- [ ] Returns correct message for valid/invalid chains
- [ ] Non-payment entries in the chain are skipped gracefully
- [ ] Empty chain returns payment_count: 0

-----

## Step 4: Dashboard Payment View

Location: `apps/dashboard` — update existing chain explorer

### What to add:

In the chain timeline (the chain explorer page built in PRUV_AGENT_BUILD.md), payment entries should be visually distinct.

**Detection:** An entry is a payment entry if `data.data.xy_proof` exists.

**Payment marker:** Use a `◆` diamond instead of `●` circle for payment entries in the timeline.

**Payment color:** Green for deposits, red for withdrawals, blue for transfers.

**Additional info shown on payment entries:**

```
◆ 9:16:03  payment.transfer                    +$250.00
│          alice → bob
│          source: stripe  ref: pi_3abc123
│          XY: a3f8...→7d2e...  ✓
```

**Expanded detail for payment entries (click to expand):**

```
┌─────────────────────────────────────────┐
│  payment.transfer                        │
│  ────────────────────────────────────    │
│  Amount:     $250.00                     │
│  Sender:     alice                       │
│  Recipient:  bob                         │
│  Source:     stripe                      │
│  Reference:  pi_3abc123                  │
│                                          │
│  Balance Proof:                          │
│  ┌─────────────┐    ┌─────────────┐     │
│  │ BEFORE (X)  │ →  │ AFTER (Y)   │     │
│  │ alice: $1000│    │ alice: $750 │     │
│  │ bob:   $500 │    │ bob:   $750 │     │
│  └─────────────┘    └─────────────┘     │
│                                          │
│  X:  a3f8c2e1b7d4...                    │
│  Y:  7d2e9a4f3c8b...                    │
│  XY: xy_b1c43e7d9a...                   │
│  ✓ Proof valid · ✓ Balanced             │
│                                          │
│  [Copy XY Proof] [Verify]               │
└─────────────────────────────────────────┘
```

**Chain summary header update:**

If the chain contains payment entries, show a payment summary alongside the existing operation summary:

```
┌─────────────────────────────────────────────┐
│  company-payments                           │
│  Feb 2026 · 847 entries · ✓ Verified        │
│                                             │
│  Payments: 412 verified · $43,291 volume    │
│  Operations: 435 verified · 0 alerts        │
└─────────────────────────────────────────────┘
```

**"Verify Payments" button:**

Next to the existing "Verify Now" button, add "Verify Payments" which calls the `/v1/chains/{id}/verify-payments` endpoint and displays the result.

### Implementation notes:

- Check if the chain explorer page exists first (it was specified in PRUV_AGENT_BUILD.md). If it doesn't exist yet, build it with payment support included from the start.
- Payment entries use the same timeline component as regular entries, just with different icon, color, and expanded fields.
- The before/after balance boxes in the detail view should be side-by-side with an arrow between them.
- Green checkmark on "Proof valid" and "Balanced". Red X if either fails.

**Acceptance criteria for Step 4:**

- [ ] Payment entries show ◆ diamond marker (not ●)
- [ ] Payment entries show amount, sender → recipient, source, reference
- [ ] Payment entries show truncated XY proof hash
- [ ] Expanded view shows before/after balance boxes
- [ ] Expanded view shows full X, Y, XY hashes
- [ ] Expanded view shows validity status
- [ ] Chain header shows payment summary (count + volume)
- [ ] "Verify Payments" button calls API and shows result
- [ ] Non-payment entries render normally (unchanged)
- [ ] Responsive on mobile

-----

## Build Order

1. **BalanceProof in xycore** — run all tests including new ones. Confirm all 301+ existing tests still pass. This is the foundation.
1. **PaymentChain in pruv** — test locally by creating a PaymentChain, doing 5 transfers, verifying. Confirm it creates proper pruv entries with xy_proof metadata.
1. **API endpoint** — deploy, test by submitting payment entries via API, then calling verify-payments.
1. **Dashboard** — update chain explorer with payment view.

**Test the full flow end-to-end:**

```python
from pruv import PaymentChain

# Create a payment ledger
ledger = PaymentChain("test-ledger", api_key="pv_live_xxx")

# Deposit funds
ledger.deposit("merchant", 10000.0, source="bank", reference="ACH-001")

# Process payments
ledger.transfer("merchant", "customer_1", 250.0, source="stripe", reference="pi_001")
ledger.transfer("merchant", "customer_2", 89.99, source="stripe", reference="pi_002")
ledger.transfer("customer_1", "merchant", 50.0, source="stripe", reference="pi_003")

# Verify everything
result = ledger.verify_payments()
print(result.message)
# ✓ 3 payments verified. All XY proofs intact. Total volume: 389.99

print(ledger.balance("merchant"))
# 9710.01

print(ledger.balance("customer_1"))
# 200.0

print(ledger.balance("customer_2"))
# 89.99
```

This should work end-to-end against the live api.pruv.dev.

Execute Step 1 now.
