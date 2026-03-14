import { describe, it, expect } from "vitest";
import { sha256, computeXY, verifyChainClientSide } from "@/lib/verify-chain";
import type { Entry } from "@/lib/types";

// ─── Helpers ──────────────────────────────────────────────────────────────

const GENESIS = "GENESIS";
const TS_EPOCH = "1700000000";
const TS_ISO = "2023-11-14T22:13:20.000Z"; // same as 1700000000

async function makeEntry(
  index: number,
  x: string,
  y: string,
  operation: string,
  timestamp: string = TS_EPOCH
): Promise<Entry> {
  const xy_proof = await computeXY(x, operation, y, timestamp);
  return {
    index,
    chain_id: "test-chain",
    x,
    y,
    xy_proof,
    timestamp:
      timestamp === TS_EPOCH
        ? new Date(Number(timestamp) * 1000).toISOString()
        : timestamp,
    actor: "system",
    action: operation,
    signed: false,
    metadata: {},
  };
}

async function makeValidChain(length: number): Promise<Entry[]> {
  const entries: Entry[] = [];
  let prevY = GENESIS;

  for (let i = 0; i < length; i++) {
    const x = prevY;
    const y = await sha256(`state-${i + 1}`);
    const entry = await makeEntry(i, x, y, `op-${i}`);
    entries.push(entry);
    prevY = y;
  }

  return entries;
}

// ─── sha256 ───────────────────────────────────────────────────────────────

describe("sha256", () => {
  it("produces a 64-character hex string", async () => {
    const result = await sha256("hello");
    expect(result).toHaveLength(64);
    expect(result).toMatch(/^[0-9a-f]{64}$/);
  });

  it("is deterministic", async () => {
    const a = await sha256("test-input");
    const b = await sha256("test-input");
    expect(a).toBe(b);
  });

  it("produces different hashes for different inputs", async () => {
    const a = await sha256("input-a");
    const b = await sha256("input-b");
    expect(a).not.toBe(b);
  });

  it("matches known SHA-256 for empty string", async () => {
    const result = await sha256("");
    expect(result).toBe(
      "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    );
  });
});

// ─── computeXY ────────────────────────────────────────────────────────────

describe("computeXY", () => {
  it("returns xy_ prefixed hash", async () => {
    const result = await computeXY("x-val", "op", "y-val", TS_EPOCH);
    expect(result).toMatch(/^xy_[0-9a-f]{64}$/);
  });

  it("is deterministic", async () => {
    const a = await computeXY("x", "op", "y", TS_EPOCH);
    const b = await computeXY("x", "op", "y", TS_EPOCH);
    expect(a).toBe(b);
  });

  it("changes when any input changes", async () => {
    const base = await computeXY("x", "op", "y", TS_EPOCH);
    const diffX = await computeXY("x2", "op", "y", TS_EPOCH);
    const diffOp = await computeXY("x", "op2", "y", TS_EPOCH);
    const diffY = await computeXY("x", "op", "y2", TS_EPOCH);
    const diffTs = await computeXY("x", "op", "y", "1700000001");

    expect(diffX).not.toBe(base);
    expect(diffOp).not.toBe(base);
    expect(diffY).not.toBe(base);
    expect(diffTs).not.toBe(base);
  });

  it("converts ISO timestamp to epoch seconds", async () => {
    const fromEpoch = await computeXY("x", "op", "y", TS_EPOCH);
    const fromISO = await computeXY("x", "op", "y", TS_ISO);
    expect(fromEpoch).toBe(fromISO);
  });
});

// ─── verifyChainClientSide ─────────────────────────────────────────────────

describe("verifyChainClientSide", () => {
  it("verifies a valid single-entry chain", async () => {
    const entries = await makeValidChain(1);
    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(true);
    expect(result.results).toHaveLength(1);
    expect(result.results[0].valid).toBe(true);
  });

  it("verifies a valid multi-entry chain", async () => {
    const entries = await makeValidChain(5);
    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(true);
    expect(result.results).toHaveLength(5);
    expect(result.results.every((r) => r.valid)).toBe(true);
  });

  it("detects non-GENESIS first entry", async () => {
    const entries = await makeValidChain(3);
    entries[0] = { ...entries[0], x: "NOT_GENESIS" };

    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(false);
    expect(result.results[0].valid).toBe(false);
    expect(result.results[0].reason).toContain("GENESIS");
  });

  it("detects broken chain link", async () => {
    const entries = await makeValidChain(3);
    // Tamper entry[1].x so it doesn't match entry[0].y
    entries[1] = { ...entries[1], x: "tampered_hash" };

    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(false);
    expect(result.results[1].valid).toBe(false);
    expect(result.results[1].reason).toContain("chain link broken");
  });

  it("detects tampered XY proof", async () => {
    const entries = await makeValidChain(3);
    // Keep valid chain links but tamper the proof
    entries[2] = { ...entries[2], xy_proof: "xy_0000000000000000000000000000000000000000000000000000000000000000" };

    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(false);
    expect(result.results[2].valid).toBe(false);
    expect(result.results[2].reason).toContain("XY proof does not match");
  });

  it("reports multiple breaks independently", async () => {
    const entries = await makeValidChain(5);
    // Break entry 0 (non-GENESIS) and entry 3 (bad proof)
    entries[0] = { ...entries[0], x: "BAD" };
    entries[3] = { ...entries[3], xy_proof: "xy_bad" };

    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(false);
    const broken = result.results.filter((r) => !r.valid);
    expect(broken.length).toBeGreaterThanOrEqual(2);
    expect(broken.some((r) => r.index === 0)).toBe(true);
    expect(broken.some((r) => r.index === 3)).toBe(true);
  });

  it("handles empty entry list", async () => {
    const result = await verifyChainClientSide([]);
    expect(result.valid).toBe(true);
    expect(result.results).toHaveLength(0);
  });

  it("validates chain rule: entry[n].x === entry[n-1].y", async () => {
    const entries = await makeValidChain(4);

    // Verify the chain rule holds for all test entries
    for (let i = 1; i < entries.length; i++) {
      expect(entries[i].x).toBe(entries[i - 1].y);
    }

    const result = await verifyChainClientSide(entries);
    expect(result.valid).toBe(true);
  });

  it("detects tampered y value (breaks proof)", async () => {
    const entries = await makeValidChain(2);
    entries[0] = { ...entries[0], y: "tampered_y_value" };

    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(false);
    // Entry 0's proof won't match because y changed
    expect(result.results[0].valid).toBe(false);
  });

  it("detects tampered operation (breaks proof)", async () => {
    const entries = await makeValidChain(2);
    entries[0] = { ...entries[0], action: "tampered-action" };

    const result = await verifyChainClientSide(entries);

    expect(result.valid).toBe(false);
    expect(result.results[0].valid).toBe(false);
    expect(result.results[0].reason).toContain("XY proof does not match");
  });
});
