"use client";

import { useEffect, useRef, useState } from "react";

export function DeeperPayments() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`deeper-payments ${visible ? "visible" : ""}`}
    >
      <div className="container">
        <p className="deeper-text">
          Some operations need more than a record. They need proof
          that the math is right.
        </p>
        <p className="deeper-text">
          Payment verification in pruv doesn&apos;t just log transfers.
          It hashes the balance state before, hashes the balance
          state after, and chains them together. If a number is wrong
          anywhere in the history, the proof breaks.
        </p>

        <div className="deeper-card">
          <div className="deeper-balances">
            <span className="deeper-label">Before:</span>
            <span className="deeper-val">merchant $10,000</span>
            <span className="deeper-sep">&middot;</span>
            <span className="deeper-val">customer $0</span>
          </div>
          <div className="deeper-balances">
            <span className="deeper-label">After:</span>
            <span className="deeper-val deeper-after">merchant &nbsp;$9,811</span>
            <span className="deeper-sep">&middot;</span>
            <span className="deeper-val deeper-after">customer $189</span>
          </div>

          <div className="deeper-proof">
            <span className="deeper-mono">
              <span className="deeper-key">X</span> &nbsp;= hash(before)
            </span>
            <span className="deeper-mono">
              <span className="deeper-key">Y</span> &nbsp;= hash(after)
            </span>
            <span className="deeper-mono">
              <span className="deeper-key">XY</span> = proof that X became Y
            </span>
          </div>

          <div className="deeper-rule">
            <span className="deeper-mono">
              Entry[N].x == Entry[N-1].y
            </span>
            <span className="deeper-mono deeper-dim">
              Break one entry, the chain breaks.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
