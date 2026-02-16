"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Copy, ExternalLink, Lock, AlertTriangle, Check, ArrowRight } from "lucide-react";
import { useState } from "react";
import { formatDistanceToNow, format } from "date-fns";
import { StateDiff } from "./state-diff";
import { getXYProof, isPaymentEntry } from "./entry-node";
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
  const isPayment = isPaymentEntry(entry);
  const xyProof = isPayment ? getXYProof(entry) : null;

  // Extract payment data from metadata.data (Agent path)
  const paymentData = entry.metadata?.data as Record<string, unknown> | undefined;
  const source = paymentData?.source as string | undefined;
  const reference = paymentData?.reference as string | undefined;
  const memo = paymentData?.memo as string | undefined ?? xyProof?.memo;

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

          {/* Payment balance proof section */}
          {isPayment && xyProof && (
            <div className="space-y-3">
              {/* Payment summary */}
              <div className="flex items-center gap-4">
                <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                  balance proof
                </h4>
                <div className="flex items-center gap-2">
                  {xyProof.valid ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium text-green-400">
                      <Check size={10} />
                      proof valid
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium text-red-400">
                      <AlertTriangle size={10} />
                      proof invalid
                    </span>
                  )}
                  <span className="text-[var(--text-tertiary)]">·</span>
                  {xyProof.balanced ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium text-green-400">
                      <Check size={10} />
                      balanced
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium text-red-400">
                      <AlertTriangle size={10} />
                      unbalanced
                    </span>
                  )}
                </div>
              </div>

              {/* Payment details grid */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {xyProof.amount !== undefined && (
                  <div>
                    <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-0.5">
                      amount
                    </div>
                    <div className="text-sm font-mono font-semibold text-[var(--text-primary)]">
                      ${xyProof.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                )}
                {xyProof.sender && (
                  <div>
                    <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-0.5">
                      sender
                    </div>
                    <div className="text-sm text-[var(--text-primary)]">{xyProof.sender}</div>
                  </div>
                )}
                {xyProof.recipient && (
                  <div>
                    <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-0.5">
                      recipient
                    </div>
                    <div className="text-sm text-[var(--text-primary)]">{xyProof.recipient}</div>
                  </div>
                )}
                {source && (
                  <div>
                    <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-0.5">
                      source
                    </div>
                    <div className="text-sm text-[var(--text-primary)]">{source}</div>
                  </div>
                )}
              </div>

              {reference && (
                <div>
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-0.5">
                    reference
                  </div>
                  <code className="text-xs font-mono text-[var(--text-secondary)]">{reference}</code>
                </div>
              )}

              {memo && (
                <div>
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-0.5">
                    memo
                  </div>
                  <div className="text-xs text-[var(--text-secondary)]">{memo}</div>
                </div>
              )}

              {/* Before/After balance boxes */}
              <div className="flex items-stretch gap-3">
                {/* Before (X) */}
                <div className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3">
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-2">
                    before (x)
                  </div>
                  <div className="space-y-1">
                    {Object.entries(xyProof.before).map(([account, balance]) => (
                      <div key={account} className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-secondary)]">{account}</span>
                        <span className="font-mono text-[var(--text-primary)]">
                          ${Number(balance).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex items-center">
                  <ArrowRight size={16} className="text-[var(--text-tertiary)]" />
                </div>

                {/* After (Y) */}
                <div className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3">
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-2">
                    after (y)
                  </div>
                  <div className="space-y-1">
                    {Object.entries(xyProof.after).map(([account, balance]) => {
                      const beforeVal = xyProof.before[account] ?? 0;
                      const afterVal = Number(balance);
                      const diff = afterVal - Number(beforeVal);
                      return (
                        <div key={account} className="flex items-center justify-between text-xs">
                          <span className="text-[var(--text-secondary)]">{account}</span>
                          <span className="flex items-center gap-1.5">
                            <span className="font-mono text-[var(--text-primary)]">
                              ${afterVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                            {diff !== 0 && (
                              <span className={`font-mono text-[10px] ${diff > 0 ? "text-green-400" : "text-red-400"}`}>
                                {diff > 0 ? "+" : ""}{diff.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </span>
                            )}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* XY proof hashes */}
              <div className="grid grid-cols-1 gap-2">
                <div>
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                    x (before hash)
                  </div>
                  <code className="block rounded-md bg-[var(--surface-secondary)] px-3 py-1.5 font-mono text-[10px] text-[var(--text-secondary)] border border-[var(--border)] truncate">
                    {xyProof.x}
                  </code>
                </div>
                <div>
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                    y (after hash)
                  </div>
                  <code className="block rounded-md bg-[var(--surface-secondary)] px-3 py-1.5 font-mono text-[10px] text-[var(--text-secondary)] border border-[var(--border)] truncate">
                    {xyProof.y}
                  </code>
                </div>
                <div>
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                    xy proof
                  </div>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 rounded-md bg-[var(--surface-secondary)] px-3 py-1.5 font-mono text-[10px] text-pruv-400 border border-[var(--border)] truncate">
                      {xyProof.xy}
                    </code>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(xyProof, null, 2), "xyproof")}
                      className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                      title="Copy XY Proof"
                    >
                      {copiedField === "xyproof" ? (
                        <Check size={14} className="text-green-400" />
                      ) : (
                        <Copy size={14} />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* State diff (for non-payment entries, or as additional detail) */}
          {!isPayment && (
            <div>
              <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-2">
                state transition (x → y)
              </h4>
              <StateDiff x={entry.x} y={entry.y} />
            </div>
          )}

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

            {/* XY proof (chain-level) */}
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
