"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface StateDiffProps {
  x: string;
  y: string;
  compact?: boolean;
}

interface DiffLine {
  type: "added" | "removed" | "unchanged" | "changed";
  key: string;
  oldValue?: string;
  newValue?: string;
  value?: string;
}

function parseState(raw: string): Record<string, string> {
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed === "object" && parsed !== null) {
      const flat: Record<string, string> = {};
      for (const [k, v] of Object.entries(parsed)) {
        flat[k] = typeof v === "string" ? v : JSON.stringify(v);
      }
      return flat;
    }
  } catch {
    // not JSON — treat as opaque string
  }
  return { _raw: raw };
}

function computeDiff(x: string, y: string): DiffLine[] {
  const xState = parseState(x);
  const yState = parseState(y);
  const allKeys = new Set([...Object.keys(xState), ...Object.keys(yState)]);
  const lines: DiffLine[] = [];

  for (const key of allKeys) {
    const xVal = xState[key];
    const yVal = yState[key];

    if (xVal === undefined) {
      lines.push({ type: "added", key, newValue: yVal });
    } else if (yVal === undefined) {
      lines.push({ type: "removed", key, oldValue: xVal });
    } else if (xVal !== yVal) {
      lines.push({ type: "changed", key, oldValue: xVal, newValue: yVal });
    } else {
      lines.push({ type: "unchanged", key, value: xVal });
    }
  }

  return lines;
}

export function StateDiff({ x, y, compact = false }: StateDiffProps) {
  const diff = useMemo(() => computeDiff(x, y), [x, y]);

  const changedLines = diff.filter((d) => d.type !== "unchanged");
  const unchangedLines = diff.filter((d) => d.type === "unchanged");
  const showUnchanged = !compact;

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-2 bg-[var(--surface-secondary)]">
        <div className="flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)]">
          <span className="text-red-400">x (before)</span>
          <ArrowRight size={12} />
          <span className="text-green-400">y (after)</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            {diff.filter((d) => d.type === "added").length} added
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-red-500" />
            {diff.filter((d) => d.type === "removed").length} removed
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-yellow-500" />
            {diff.filter((d) => d.type === "changed").length} changed
          </span>
        </div>
      </div>

      {/* Diff body */}
      <div className="font-mono text-xs leading-6 divide-y divide-[var(--border)]">
        {changedLines.map((line, i) => (
          <motion.div
            key={`${line.key}-${i}`}
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 }}
          >
            {line.type === "added" && (
              <div className="diff-added px-4 py-1.5 flex items-center gap-2">
                <span className="text-green-500 font-semibold w-4">+</span>
                <span className="text-[var(--text-secondary)]">
                  {line.key}:
                </span>
                <span className="text-green-400">{line.newValue}</span>
              </div>
            )}
            {line.type === "removed" && (
              <div className="diff-removed px-4 py-1.5 flex items-center gap-2">
                <span className="text-red-500 font-semibold w-4">-</span>
                <span className="text-[var(--text-secondary)]">
                  {line.key}:
                </span>
                <span className="text-red-400">{line.oldValue}</span>
              </div>
            )}
            {line.type === "changed" && (
              <div className="diff-changed px-4 py-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-yellow-500 font-semibold w-4">~</span>
                  <span className="text-[var(--text-secondary)]">
                    {line.key}:
                  </span>
                </div>
                <div className="ml-6 mt-0.5 flex items-center gap-2">
                  <span className="text-red-400 line-through opacity-60">
                    {line.oldValue}
                  </span>
                  <ArrowRight size={10} className="text-[var(--text-tertiary)]" />
                  <span className="text-green-400">{line.newValue}</span>
                </div>
              </div>
            )}
          </motion.div>
        ))}

        {showUnchanged && unchangedLines.length > 0 && (
          <div className="px-4 py-2 space-y-0.5">
            <div className="text-[var(--text-tertiary)] text-[10px] uppercase tracking-wider mb-1">
              unchanged ({unchangedLines.length})
            </div>
            {unchangedLines.map((line) => (
              <div
                key={line.key}
                className="flex items-center gap-2 text-[var(--text-tertiary)] opacity-60"
              >
                <span className="w-4" />
                <span>{line.key}:</span>
                <span>{line.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
