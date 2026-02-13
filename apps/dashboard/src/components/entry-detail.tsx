"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Copy, ExternalLink, Lock, AlertTriangle, Check } from "lucide-react";
import { useState } from "react";
import { formatDistanceToNow, format } from "date-fns";
import { StateDiff } from "./state-diff";
import type { Entry, EntryValidation } from "@/lib/types";

interface EntryDetailProps {
  entry: Entry;
  validation?: EntryValidation;
  chainId: string;
}

export function EntryDetail({
  entry,
  validation,
  chainId,
}: EntryDetailProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const isBroken = validation && !validation.valid;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: "auto" }}
        exit={{ opacity: 0, height: 0 }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
        className="overflow-hidden"
      >
        <div className="ml-14 mb-6 space-y-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          {/* Validation status */}
          {validation && (
            <div
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                isBroken
                  ? "bg-red-500/10 text-red-400 border border-red-500/20"
                  : "bg-green-500/10 text-green-400 border border-green-500/20"
              }`}
            >
              {isBroken ? (
                <>
                  <AlertTriangle size={14} />
                  <span>
                    chain broken at this entry
                    {validation.reason && ` — ${validation.reason}`}
                  </span>
                </>
              ) : (
                <>
                  <Check size={14} />
                  <span>entry verified — x matches previous y, proof valid</span>
                </>
              )}
            </div>
          )}

          {/* State diff */}
          <div>
            <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              state transition (x → y)
            </h4>
            <StateDiff x={entry.x} y={entry.y} />
          </div>

          {/* Metadata grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Timestamp */}
            <div>
              <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                timestamp
              </div>
              <div className="text-sm text-[var(--text-primary)]">
                {format(new Date(entry.timestamp), "MMM d, yyyy HH:mm:ss")}
              </div>
              <div className="text-xs text-[var(--text-tertiary)]">
                {formatDistanceToNow(new Date(entry.timestamp), {
                  addSuffix: true,
                })}
              </div>
            </div>

            {/* Actor */}
            <div>
              <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                actor
              </div>
              <div className="text-sm text-[var(--text-primary)]">
                {entry.actor}
              </div>
            </div>

            {/* XY proof */}
            <div className="col-span-2">
              <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                xy proof hash
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 rounded-md bg-[var(--surface-secondary)] px-3 py-1.5 font-mono text-xs text-pruv-400 border border-[var(--border)] truncate">
                  {entry.xy_proof}
                </code>
                <button
                  onClick={() => copyToClipboard(entry.xy_proof, "proof")}
                  className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                >
                  {copiedField === "proof" ? (
                    <Check size={14} className="text-green-400" />
                  ) : (
                    <Copy size={14} />
                  )}
                </button>
              </div>
            </div>

            {/* Signature */}
            {entry.signed && entry.signature && (
              <div className="col-span-2">
                <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Lock size={10} className="text-pruv-400" />
                  signature
                </div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded-md bg-[var(--surface-secondary)] px-3 py-1.5 font-mono text-xs text-[var(--text-secondary)] border border-[var(--border)] truncate">
                    {entry.signature}
                  </code>
                  <button
                    onClick={() =>
                      copyToClipboard(entry.signature!, "signature")
                    }
                    className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    {copiedField === "signature" ? (
                      <Check size={14} className="text-green-400" />
                    ) : (
                      <Copy size={14} />
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Link to full detail page */}
          <div className="pt-2 border-t border-[var(--border)]">
            <a
              href={`/chains/${chainId}/entries/${entry.index}`}
              className="inline-flex items-center gap-1.5 text-xs text-pruv-400 hover:text-pruv-300 transition-colors"
            >
              <ExternalLink size={12} />
              view full entry detail
            </a>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
