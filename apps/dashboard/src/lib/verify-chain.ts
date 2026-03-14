import type { Entry } from "./types";

export async function sha256(message: string): Promise<string> {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function computeXY(
  x: string,
  operation: string,
  y: string,
  timestamp: string
): Promise<string> {
  const ts =
    typeof timestamp === "string" && !timestamp.includes("T")
      ? timestamp
      : String(Math.floor(new Date(timestamp).getTime() / 1000));
  const message = `${x}:${operation}:${y}:${ts}`;
  const hash = await sha256(message);
  return `xy_${hash}`;
}

export interface VerificationEntry {
  index: number;
  valid: boolean;
  reason?: string;
}

export interface VerificationResult {
  valid: boolean;
  results: VerificationEntry[];
}

export async function verifyChainClientSide(
  entries: Entry[]
): Promise<VerificationResult> {
  const results: VerificationEntry[] = [];
  let allValid = true;

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];

    // Check chain rule
    if (i === 0) {
      if (entry.x !== "GENESIS") {
        results.push({
          index: i,
          valid: false,
          reason: `first entry x should be "GENESIS", got "${entry.x.slice(0, 16)}..."`,
        });
        allValid = false;
        continue;
      }
    } else {
      const prevY = entries[i - 1].y;
      if (entry.x !== prevY) {
        results.push({
          index: i,
          valid: false,
          reason: `x does not match previous entry y — chain link broken`,
        });
        allValid = false;
        continue;
      }
    }

    // Recompute XY proof
    const expectedXY = await computeXY(
      entry.x,
      entry.action,
      entry.y,
      entry.timestamp
    );
    if (entry.xy_proof !== expectedXY) {
      results.push({
        index: i,
        valid: false,
        reason: "recomputed XY proof does not match stored proof",
      });
      allValid = false;
      continue;
    }

    results.push({ index: i, valid: true });
  }

  return { valid: allValid, results };
}
