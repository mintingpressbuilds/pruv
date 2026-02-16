"use client";

export function ReceiptCard() {
  return (
    <div className="receipt-card">
      <div className="rc-title">receipt</div>

      <div className="rc-rows">
        <div className="rc-row">
          <span className="rc-key">action</span>
          <span className="rc-val">send_email</span>
        </div>
        <div className="rc-row">
          <span className="rc-key">sequence</span>
          <span className="rc-val">#3 of 47</span>
        </div>
        <div className="rc-row">
          <span className="rc-key">timestamp</span>
          <span className="rc-val">2026-02-15T12:00:03Z</span>
        </div>
      </div>

      <div className="rc-hash-section">
        <div className="rc-hash-label">hash</div>
        <div className="rc-hash">b1c43e7d9a4f2b8c1d5e6f7a8b9c0d1e</div>
      </div>

      <div className="rc-hash-section">
        <div className="rc-hash-label">previous</div>
        <div className="rc-hash">7d2e9a4f3c8b1d6e5f2a7c4b9d0e8f1a</div>
      </div>

      <div className="rc-verified">
        <span className="rc-check">{"\u2713"} verified</span>
        <p>
          This receipt is cryptographically linked to every action before it.
          Tamper with any entry and this receipt becomes invalid.
        </p>
      </div>
    </div>
  );
}
