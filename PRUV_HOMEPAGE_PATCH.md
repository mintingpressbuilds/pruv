# PRUV HOMEPAGE PATCH — Payment Verification

## What this changes

This is a patch to PRUV_HOMEPAGE_V2.md. It updates ONE tab in the "Works everywhere"
section and adds ONE small section after it. Nothing else changes.

- Hero: unchanged
- Tagline: unchanged
- Protocol demo: unchanged (still shows invoice-trail, not payments)
- All other tabs: unchanged
- Decorator section: unchanged
- Framework integrations: unchanged
- Alerts: unchanged
- Receipt card: unchanged
- How it works: unchanged
- Install: unchanged
- Footer: unchanged

-----

## CHANGE 1: Replace the Payments tab in Section 3

In PRUV_HOMEPAGE_V2.md Section 3 ("Works everywhere"), replace ONLY the
Payments tab code snippet with this:

**Payments**

```python
from pruv import PaymentChain

ledger = PaymentChain("order-7291", api_key="pv_live_xxx")

ledger.deposit("merchant", 10000.00, source="bank", reference="ACH-4401")
ledger.transfer("merchant", "customer_123", 189.00, source="stripe", reference="pi_3abc")
ledger.transfer("merchant", "customer_456", 64.50, source="stripe", reference="pi_3def")

result = ledger.verify_payments()
# ✓ 2 payments verified · all XY proofs intact
# ✓ balances before and after — cryptographically linked
# ✓ conservation of value confirmed
# ✓ total volume: $253.50
```

This replaces the previous Payments tab which used generic `Chain()` with `chain.add()`.

The difference is visible: PaymentChain is a real class. `deposit`, `transfer`,
`verify_payments` are real methods. The comments show what verification actually checks —
XY proofs, balance linkage, conservation of value. Developers reading this see that
payments get deeper verification than generic operations, without being told.

All other tabs (AI Agents, Compliance, CI/CD, Supply Chain, Legal) stay exactly the same.

-----

## CHANGE 2: Add one line to the Payments tab comment

Below the Payments tab (where each tab has its one-line description as a code comment),
the payments comment should be:

```
# balances verified. state transitions proven. every dollar accounted for.
```

This replaces whatever generic comment was there before. It signals depth without
a paragraph of explanation.

-----

## CHANGE 3: Add "Deeper where it matters" mini-section

Insert this between Section 3 (Works everywhere) and Section 4 (The decorator).
It should feel like a natural continuation, not a separate section with a big header.

Visual treatment: same dark background, same typography. No section header.
Just a quiet statement with a small code block. It should feel like a footnote
that rewards people who are reading carefully.

```
Some operations need more than a record. They need proof
that the math is right.

Payment verification in pruv doesn't just log transfers.
It hashes the balance state before, hashes the balance
state after, and chains them together. If a number is wrong
anywhere in the history, the proof breaks.

    Before:  merchant $10,000  ·  customer $0
    After:   merchant  $9,811  ·  customer $189

    X  = hash(before)
    Y  = hash(after)
    XY = proof that X became Y

    Entry[N].x == Entry[N-1].y
    Break one entry, the chain breaks.
```

That's it. No "learn more" button. No call to action. No feature comparison.
Just a quiet demonstration that pruv goes deeper on payments than anyone
would expect from a verification API.

-----

## WHY THIS WORKS

The homepage says "operational proof for any system." Six tabs prove it works everywhere.

But the Payments tab is slightly different from the others. It shows `PaymentChain`
instead of `Chain`. It shows `verify_payments()` instead of `verify()`. It shows
balance checking, conservation of value, XY proofs.

A careful reader notices: "Wait, this one does more." That's the hook. They don't
need to understand BalanceProof or xychain or the XY state model. They just see that
payments get special treatment. If they're building anything with money, that's
the moment they decide to try pruv.

The quiet "Deeper where it matters" section confirms what they noticed. It shows
the before/after balance hashing in plain text. No jargon. No buzzwords. Just:
here's what we hash, here's why it breaks if you tamper.

The tagline stays clean. The positioning stays universal. Payments are just the
sharpest edge of the same knife.

-----

## IMPLEMENTATION

When building the homepage from PRUV_HOMEPAGE_V2.md:

1. Build everything exactly as specified in PRUV_HOMEPAGE_V2.md
1. Replace the Payments tab content with the PaymentChain snippet above
1. Insert the "Deeper where it matters" mini-section between Section 3 and Section 4
1. Everything else is unchanged

The mini-section should have:

- No header tag (no h2, no h3) — it's a continuation, not a new section
- Slightly larger line-height than body text
- The before/after balance display should be styled like the chain demo —
  monospace, dark card, subtle border
- The `X = hash(before)` lines should be in a code-style block but
  NOT a full code block — more like inline monospace text
- Subtle fade-in animation when scrolled into view (same as other sections)
