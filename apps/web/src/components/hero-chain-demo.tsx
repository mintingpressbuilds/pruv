"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const CODE_LINES = [
  { type: "kw", text: "import " },
  { type: "var", text: "pruv" },
  { type: "plain", text: "\n\n" },
  { type: "var", text: "agent" },
  { type: "plain", text: " = " },
  { type: "var", text: "pruv" },
  { type: "plain", text: "." },
  { type: "fn", text: "Agent" },
  { type: "plain", text: "(" },
  { type: "str", text: '"email-assistant"' },
  { type: "plain", text: ")\n\n" },
  { type: "var", text: "agent" },
  { type: "plain", text: "." },
  { type: "fn", text: "action" },
  { type: "plain", text: "(" },
  { type: "str", text: '"read_inbox"' },
  { type: "plain", text: ", {" },
  { type: "str", text: '"count"' },
  { type: "plain", text: ": 12})\n" },
  { type: "var", text: "agent" },
  { type: "plain", text: "." },
  { type: "fn", text: "action" },
  { type: "plain", text: "(" },
  { type: "str", text: '"draft_reply"' },
  { type: "plain", text: ", {" },
  { type: "str", text: '"to"' },
  { type: "plain", text: ": " },
  { type: "str", text: '"sarah@co.com"' },
  { type: "plain", text: "})\n" },
  { type: "var", text: "agent" },
  { type: "plain", text: "." },
  { type: "fn", text: "action" },
  { type: "plain", text: "(" },
  { type: "str", text: '"send_email"' },
  { type: "plain", text: ", {" },
  { type: "str", text: '"subject"' },
  { type: "plain", text: ": " },
  { type: "str", text: '"Re: Q3"' },
  { type: "plain", text: "})\n\n" },
  { type: "var", text: "chain" },
  { type: "plain", text: " = " },
  { type: "var", text: "agent" },
  { type: "plain", text: "." },
  { type: "fn", text: "verify" },
  { type: "plain", text: "()\n" },
  { type: "cm", text: "# \u2713 3 actions \u00b7 all verified \u00b7 chain intact" },
];

interface DemoEntry {
  seq: number;
  action: string;
  time: string;
  hash: string;
  prev: string | null;
}

const ENTRIES: DemoEntry[] = [
  { seq: 1, action: "read_inbox", time: "12:00:01.003", hash: "a3f8c2e1b7d4", prev: null },
  { seq: 2, action: "draft_reply", time: "12:00:02.847", hash: "7d2e9a4f3c8b", prev: "a3f8c2e1b7d4" },
  { seq: 3, action: "send_email", time: "12:00:03.201", hash: "b1c43e7d9a4f", prev: "7d2e9a4f3c8b" },
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
          <span className="hdc-name">email-assistant</span>
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
            chain intact &middot; each hash includes the previous hash
          </div>
        )}
      </div>
    </div>
  );
}
