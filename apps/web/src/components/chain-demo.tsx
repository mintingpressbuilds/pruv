"use client";

import { useState, useCallback, useRef } from "react";

interface ChainEntry {
  index: number;
  operation: string;
  x: string;
  y: string;
  xy: string;
  ts: number;
  x_state: Record<string, unknown> | null;
  y_state: Record<string, unknown>;
  _tampered?: boolean;
}

const OPERATIONS = [
  { op: "genesis", x_state: null, y_state: { status: "initialized", version: "1.0.0" } },
  { op: "file.read", x_state: { files: 0 }, y_state: { files: 1, last: "main.py" } },
  { op: "file.write", x_state: { "main.py": "def hello(): pass", lines: 1 }, y_state: { "main.py": "def hello():\\n  return 'world'", lines: 2 } },
  { op: "test.run", x_state: { tests: 0, passing: 0 }, y_state: { tests: 3, passing: 3 } },
  { op: "deploy", x_state: { deployed: false, url: null }, y_state: { deployed: true, url: "https://app.example.com" } },
  { op: "verify", x_state: { health: "unknown" }, y_state: { health: "200 OK", latency: "142ms" } },
];

function sha256(str: string): string {
  let h = 0x6a09e667;
  let a = 0xbb67ae85;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 0x9e3779b1);
    a = Math.imul(a ^ str.charCodeAt(i), 0x5f356495);
  }
  h = h >>> 0;
  a = a >>> 0;
  return (
    h.toString(16).padStart(8, "0") +
    a.toString(16).padStart(8, "0") +
    (h ^ a).toString(16).padStart(8, "0") +
    ((h + a) >>> 0).toString(16).padStart(8, "0")
  );
}

function hashState(state: Record<string, unknown>): string {
  return sha256(JSON.stringify(state));
}

function computeXY(x: string, op: string, y: string, ts: number): string {
  return "xy_" + sha256(`${x}:${op}:${y}:${ts}`);
}

export function ChainDemo() {
  const [chain, setChain] = useState<ChainEntry[]>([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [tampered, setTampered] = useState(false);
  const [tamperDisabled, setTamperDisabled] = useState(true);
  const [verifyDisabled, setVerifyDisabled] = useState(true);
  const [showRestore, setShowRestore] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    show: boolean;
    valid: boolean;
    message: string;
    detail: string;
  } | null>(null);

  const chainRef = useRef<ChainEntry[]>([]);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const buildChain = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];

    const newChain: ChainEntry[] = [];
    let prevY = "GENESIS";

    OPERATIONS.forEach((item, i) => {
      const x = prevY;
      const y = hashState(item.y_state);
      const ts = Date.now() + i;
      const xy = computeXY(x, item.op, y, ts);

      newChain.push({
        index: i,
        operation: item.op,
        x,
        y,
        xy,
        ts,
        x_state: item.x_state,
        y_state: item.y_state,
      });
      prevY = y;
    });

    chainRef.current = newChain;
    setChain(newChain);
    setVisibleCount(0);
    setExpandedIndex(null);
    setTampered(false);
    setTamperDisabled(true);
    setVerifyDisabled(true);
    setShowRestore(false);
    setVerifyResult(null);

    OPERATIONS.forEach((_, i) => {
      const timer = setTimeout(() => {
        setVisibleCount((c) => c + 1);
      }, (i + 1) * 200);
      timersRef.current.push(timer);
    });

    const enableTimer = setTimeout(() => {
      setTamperDisabled(false);
      setVerifyDisabled(false);
    }, OPERATIONS.length * 200);
    timersRef.current.push(enableTimer);
  }, []);

  const tamperEntry = useCallback(() => {
    if (chainRef.current.length < 4) return;

    const updated = [...chainRef.current];
    updated[3] = {
      ...updated[3],
      y: sha256("TAMPERED_STATE_" + Math.random()),
      _tampered: true,
    };

    chainRef.current = updated;
    setChain(updated);
    setTampered(true);
    setTamperDisabled(true);
  }, []);

  const verifyChain = useCallback(() => {
    const entries = chainRef.current;
    let valid = true;
    let breakIndex: number | null = null;

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];
      const expectedXY = computeXY(entry.x, entry.operation, entry.y, entry.ts);

      if (expectedXY !== entry.xy) {
        valid = false;
        breakIndex = i;
        break;
      }

      if (i === 0) {
        if (entry.x !== "GENESIS") {
          valid = false;
          breakIndex = i;
          break;
        }
      } else {
        if (entry.x !== entries[i - 1].y) {
          valid = false;
          breakIndex = i;
          break;
        }
      }
    }

    if (valid) {
      setVerifyResult({
        show: true,
        valid: true,
        message: "\u2713 Chain intact",
        detail: `${entries.length} entries verified. No tampering detected.`,
      });
      setShowRestore(false);
    } else {
      setVerifyResult({
        show: true,
        valid: false,
        message: `\u2717 Chain broken at entry ${breakIndex}`,
        detail: `Entry ${breakIndex} failed verification. Y hash does not match expected value.`,
      });
      setShowRestore(true);
    }
  }, []);

  const restoreChain = useCallback(() => {
    buildChain();
  }, [buildChain]);

  const toggleEntry = useCallback((index: number) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  }, []);

  return (
    <>
      <div className="chain-controls">
        <button className="btn" onClick={buildChain}>
          Build chain
        </button>
        <button
          className={`btn danger${tampered ? " active" : ""}`}
          onClick={tamperEntry}
          disabled={tamperDisabled}
        >
          Tamper entry 3
        </button>
        <button
          className="btn"
          onClick={verifyChain}
          disabled={verifyDisabled}
        >
          Verify
        </button>
        {showRestore && (
          <button className="btn" onClick={restoreChain}>
            Restore
          </button>
        )}
      </div>

      <div className="chain-demo">
        <div className="chain-line" />
        {chain.slice(0, visibleCount).map((entry) => (
          <div key={entry.index} className="chain-entry">
            <div
              className={`chain-dot${entry.index === 0 ? " genesis" : ""}${entry._tampered ? " tampered" : ""}`}
            />
            <div
              className={`entry-card${entry._tampered ? " tampered" : ""}${expandedIndex === entry.index ? " expanded" : ""}`}
              onClick={() => toggleEntry(entry.index)}
            >
              <div className="entry-header">
                <span className="entry-op">{entry.operation}</span>
                <span className="entry-index">#{entry.index}</span>
              </div>
              <div className="entry-hash">
                <span className="label">xy </span>
                <span
                  className="val"
                  style={entry._tampered ? { color: "var(--red)" } : undefined}
                >
                  {entry.xy.substring(0, 24)}&hellip;
                </span>
              </div>
              <div className="entry-detail">
                <div className="state-diff">
                  <div className="state-box">
                    <div className="state-label">X (before)</div>
                    {entry.x_state ? (
                      Object.entries(entry.x_state).map(([k, v]) => (
                        <div key={k} className="unchanged">
                          {k}: {String(v)}
                        </div>
                      ))
                    ) : (
                      <div className="unchanged">GENESIS</div>
                    )}
                    <div style={{ marginTop: 8, color: "var(--dim)" }}>
                      hash: {entry.x.substring(0, 16)}&hellip;
                    </div>
                  </div>
                  <div className="state-box">
                    <div className="state-label">Y (after)</div>
                    {Object.entries(entry.y_state).map(([k, v]) => (
                      <div key={k} className="added">
                        {k}: {String(v)}
                      </div>
                    ))}
                    <div style={{ marginTop: 8, color: "var(--dim)" }}>
                      hash: {entry.y.substring(0, 16)}&hellip;
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {verifyResult?.show && (
        <div
          className={`verify-result show${verifyResult.valid ? " valid" : " broken"}`}
        >
          <span
            className={`status${verifyResult.valid ? " valid-text" : " broken-text"}`}
          >
            {verifyResult.message}
          </span>
          <br />
          <span style={{ color: "var(--dim)" }}>{verifyResult.detail}</span>
        </div>
      )}
    </>
  );
}
