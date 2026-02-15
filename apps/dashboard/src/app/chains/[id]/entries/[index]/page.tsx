"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Lock,
  AlertTriangle,
  Check,
  Copy,
  ExternalLink,
} from "lucide-react";
import { useState } from "react";
import { format, formatDistanceToNow } from "date-fns";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { StateDiff } from "@/components/state-diff";
import { useChain } from "@/hooks/use-chains";
import { useEntry, useEntryValidation } from "@/hooks/use-entries";

export default function EntryDetailPage() {
  const params = useParams();
  const chainId = params.id as string;
  const entryIndex = parseInt(params.index as string, 10);

  const { data: chain } = useChain(chainId);
  const { data: entry, isLoading } = useEntry(chainId, entryIndex);
  const { data: validation } = useEntryValidation(chainId, entryIndex);
  const { data: prevEntry } = useEntry(chainId, entryIndex - 1);

  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const isBroken = validation && !validation.valid;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        <Header
          title={`entry #${entryIndex}`}
          subtitle={chain?.name}
          actions={
            <div className="flex items-center gap-2">
              {entryIndex > 0 && (
                <Link
                  href={`/chains/${chainId}/entries/${entryIndex - 1}`}
                  className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                >
                  <ArrowLeft size={12} />
                  entry #{entryIndex - 1}
                </Link>
              )}
              <Link
                href={`/chains/${chainId}/entries/${entryIndex + 1}`}
                className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                entry #{entryIndex + 1}
                <ArrowRight size={12} />
              </Link>
            </div>
          }
        />

        <main className="p-6 space-y-6">
          {isLoading ? (
            <div className="space-y-4">
              <div className="h-20 rounded-xl bg-[var(--surface-secondary)] animate-pulse border border-[var(--border)]" />
              <div className="h-48 rounded-xl bg-[var(--surface-secondary)] animate-pulse border border-[var(--border)]" />
            </div>
          ) : !entry ? (
            <div className="flex flex-col items-center py-16 text-center">
              <p className="text-sm text-[var(--text-secondary)]">
                entry not found
              </p>
              <Link
                href={`/chains/${chainId}`}
                className="mt-2 text-xs text-pruv-400 hover:text-pruv-300"
              >
                back to chain
              </Link>
            </div>
          ) : (
            <>
              {/* Validation status */}
              {validation && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex items-center gap-3 rounded-xl border p-4 ${
                    isBroken
                      ? "border-red-500/20 bg-red-500/5 text-red-400"
                      : "border-green-500/20 bg-green-500/5 text-green-400"
                  }`}
                >
                  {isBroken ? (
                    <AlertTriangle size={18} />
                  ) : (
                    <Check size={18} />
                  )}
                  <div>
                    <p className="text-sm font-medium">
                      {isBroken
                        ? "chain integrity broken at this entry"
                        : "entry verified — chain integrity intact"}
                    </p>
                    <p className="text-xs opacity-70 mt-0.5">
                      {isBroken
                        ? validation.reason ?? "entry[n].x != entry[n-1].y"
                        : "entry[n].x == entry[n-1].y, proof valid"}
                    </p>
                  </div>
                </motion.div>
              )}

              {/* Entry metadata */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-mono font-bold text-pruv-400">
                      #{entry.index}
                    </span>
                    <span className="text-sm font-medium text-[var(--text-primary)]">
                      {entry.action}
                    </span>
                    {entry.signed && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-pruv-500/10 px-2 py-0.5 text-[10px] font-medium text-pruv-400 border border-pruv-500/20">
                        <Lock size={10} />
                        signed
                      </span>
                    )}
                  </div>
                  <Link
                    href={`/chains/${chainId}`}
                    className="flex items-center gap-1 text-xs text-pruv-400 hover:text-pruv-300"
                  >
                    <ExternalLink size={10} />
                    view chain
                  </Link>
                </div>

                <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                  <div>
                    <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                      actor
                    </div>
                    <div className="text-sm text-[var(--text-primary)]">
                      {entry.actor}
                    </div>
                  </div>
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
                  <div className="col-span-2">
                    <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
                      xy proof hash
                    </div>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 rounded-md bg-[var(--surface)] px-3 py-1.5 font-mono text-xs text-pruv-400 border border-[var(--border)] truncate">
                        {entry.xy_proof}
                      </code>
                      <button
                        onClick={() => copyToClipboard(entry.xy_proof, "proof")}
                        className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                      >
                        {copiedField === "proof" ? (
                          <Check size={14} className="text-green-400" />
                        ) : (
                          <Copy size={14} />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Full state diff */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                  state transition (x → y)
                </h3>
                <StateDiff x={entry.x} y={entry.y} />
              </motion.div>

              {/* Chain link verification */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5"
              >
                <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-4">
                  chain link integrity
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                    <span className="text-xs text-[var(--text-secondary)]">
                      x (input state hash)
                    </span>
                    <code className="font-mono text-xs text-[var(--text-primary)] max-w-xs truncate">
                      {entry.x}
                    </code>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                    <span className="text-xs text-[var(--text-secondary)]">
                      y (output state hash)
                    </span>
                    <code className="font-mono text-xs text-[var(--text-primary)] max-w-xs truncate">
                      {entry.y}
                    </code>
                  </div>

                  {prevEntry && (
                    <div
                      className={`flex items-center gap-3 rounded-lg p-3 border ${
                        entry.x === prevEntry.y
                          ? "border-green-500/20 bg-green-500/5"
                          : "border-red-500/20 bg-red-500/5"
                      }`}
                    >
                      {entry.x === prevEntry.y ? (
                        <Check size={14} className="text-green-400" />
                      ) : (
                        <AlertTriangle size={14} className="text-red-400" />
                      )}
                      <div className="text-xs">
                        {entry.x === prevEntry.y ? (
                          <span className="text-green-400">
                            valid — entry[{entryIndex}].x == entry[
                            {entryIndex - 1}].y
                          </span>
                        ) : (
                          <span className="text-red-400">
                            broken — entry[{entryIndex}].x != entry[
                            {entryIndex - 1}].y
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {entryIndex === 0 && (
                    <div className="flex items-center gap-3 rounded-lg p-3 border border-pruv-500/20 bg-pruv-500/5">
                      <div className="h-2 w-2 rounded-full bg-pruv-500" />
                      <span className="text-xs text-pruv-400">
                        genesis entry — chain origin
                      </span>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Signature */}
              {entry.signed && entry.signature && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5"
                >
                  <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <Lock size={12} className="text-pruv-400" />
                    digital signature
                  </h3>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 rounded-md bg-[var(--surface)] px-3 py-2 font-mono text-xs text-[var(--text-secondary)] border border-[var(--border)] break-all">
                      {entry.signature}
                    </code>
                    <button
                      onClick={() =>
                        copyToClipboard(entry.signature!, "sig")
                      }
                      className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      {copiedField === "sig" ? (
                        <Check size={14} className="text-green-400" />
                      ) : (
                        <Copy size={14} />
                      )}
                    </button>
                  </div>
                </motion.div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
