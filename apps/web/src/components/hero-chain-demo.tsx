"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const CODE_LINES = [
  { type: "kw", text: "from " },
  { type: "var", text: "pruv" },
  { type: "kw", text: " import " },
  { type: "fn", text: "Chain" },
  { type: "plain", text: "\n\n" },
  { type: "var", text: "chain" },
  { type: "plain", text: " = " },
  { type: "fn", text: "Chain" },
  { type: "plain", text: "(" },
  { type: "str", text: '"invoice-trail"' },
  { type: "plain", text: ")\n\n" },
  { type: "var", text: "chain" },
  { type: "plain", text: "." },
  { type: "fn", text: "add" },
  { type: "plain", text: "(" },
  { type: "str", text: '"invoice_created"' },
  { type: "plain", text: ", {" },
  { type: "str", text: '"id"' },
  { type: "plain", text: ": " },
  { type: "str", text: '"INV-0042"' },
  { type: "plain", text: ", " },
  { type: "str", text: '"amount"' },
  { type: "plain", text: ": 240.00})\n" },
  { type: "var", text: "chain" },
  { type: "plain", text: "." },
  { type: "fn", text: "add" },
  { type: "plain", text: "(" },
  { type: "str", text: '"payment_received"' },
  { type: "plain", text: ", {" },
  { type: "str", text: '"method"' },
  { type: "plain", text: ": " },
  { type: "str", text: '"ach"' },
  { type: "plain", text: ", " },
  { type: "str", text: '"ref"' },
  { type: "plain", text: ": " },
  { type: "str", text: '"TXN-8812"' },
  { type: "plain", text: "})\n" },
  { type: "var", text: "chain" },
  { type: "plain", text: "." },
  { type: "fn", text: "add" },
  { type: "plain", text: "(" },
  { type: "str", text: '"receipt_issued"' },
  { type: "plain", text: ", {" },
  { type: "str", text: '"to"' },
  { type: "plain", text: ": " },
  { type: "str", text: '"sarah@company.com"' },
  { type: "plain", text: "})\n\n" },
  { type: "var", text: "chain" },
  { type: "plain", text: "." },
  { type: "fn", text: "verify" },
  { type: "plain", text: "()\n" },
  { type: "cm", text: "# \u2713 3 entries \u00b7 chain intact \u00b7 tamper-proof" },
];

interface DemoEntry {
  seq: number;
  action: string;
  time: string;
  hash: string;
  prev: string | null;
}

const ENTRIES: DemoEntry[] = [
  { seq: 1, action: "invoice_created", time: "12:00:01", hash: "a3f8c2e1b7d4", prev: null },
  { seq: 2, action: "payment_received", time: "12:00:03", hash: "7d2e9a4f3c8b", prev: "a3f8c2e1b7d4" },
  { seq: 3, action: "receipt_issued", time: "12:00:04", hash: "b1c43e7d9a4f", prev: "7d2e9a4f3c8b" },
];

function TypedHash({ hash, delay }: { hash: string; delay: number }) {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    if (visible >= hash.length) return;
    const t = setTimeout(() => setVisible((v) => v + 1), 35);
    return () => clearTimeout(t);
  }, [visible, hash.length]);

  useEffect(() => {
    const t = setTimeout(() => setVisible(1), delay);
    return () => clearTimeout(t);
  }, [delay]);

  return <>{hash.slice(0, visible)}{visible < hash.length ? "\u2588" : "\u2026"}</>;
}

export function HeroChainDemo() {
  const [visibleEntries, setVisibleEntries] = useState(0);
  const [verified, setVerified] = useState(false);
  const [started, setStarted] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const start = useCallback(() => {
    if (started) return;
    setStarted(true);
    setVisibleEntries(0);
    setVerified(false);

    ENTRIES.forEach((_, i) => {
      setTimeout(() => setVisibleEntries(i + 1), (i + 1) * 800);
    });
    setTimeout(() => setVerified(true), ENTRIES.length * 800 + 600);
  }, [started]);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) start(); },
      { threshold: 0.3 }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [start]);

  return (
    <div className="hero-demo" ref={ref}>
      {/* Code side */}
      <div className="hero-demo-code">
        <div className="hero-demo-label">python</div>
        <pre>
          <code>
            {CODE_LINES.map((tok, i) => {
              const cls =
                tok.type === "kw" ? "cb-kw" :
                tok.type === "fn" ? "cb-fn" :
                tok.type === "str" ? "cb-str" :
                tok.type === "cm" ? "cb-cm" :
                tok.type === "var" ? "cb-var" :
                "";
              return cls ? <span key={i} className={cls}>{tok.text}</span> : <span key={i}>{tok.text}</span>;
            })}
          </code>
        </pre>
      </div>

      {/* Chain output side */}
      <div className="hero-demo-chain">
        <div className="hero-demo-label">chain output</div>
        <div className="hdc-header">
          <span className="hdc-name">invoice-trail</span>
          {verified && <span className="hdc-status">{"\u2713"} verified</span>}
        </div>

        <div className="hdc-entries">
          {ENTRIES.slice(0, visibleEntries).map((entry, i) => (
            <div key={entry.seq} className="hdc-entry" style={{ animationDelay: `${i * 100}ms` }}>
              <div className="hdc-dot" />
              {i > 0 && <div className="hdc-line" />}
              <div className="hdc-content">
                <div className="hdc-row">
                  <span className="hdc-seq">#{entry.seq}</span>
                  <span className="hdc-action">{entry.action}</span>
                  <span className="hdc-time">{entry.time}</span>
                </div>
                <div className="hdc-hash">
                  hash: <TypedHash hash={entry.hash} delay={i * 800 + 200} />
                </div>
                {entry.prev && (
                  <div className="hdc-prev">
                    prev: {entry.prev.slice(0, 8)}&hellip;
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {verified && (
          <div className="hdc-footer">
            <span className="hdc-check">{"\u2713"}</span>
            {" "}chain intact &middot; each hash includes the previous hash.
            <br />change any entry and the chain breaks.
          </div>
        )}
      </div>
    </div>
  );
}
