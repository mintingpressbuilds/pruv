"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldCheck,
  ShieldX,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { format } from "date-fns";
import { useSharedChain } from "@/hooks/use-shared-chain";
import {
  verifyChainClientSide,
  type VerificationEntry,
} from "@/lib/verify-chain";
import type { Entry } from "@/lib/types";

// ─── Components ────────────────────────────────────────────────────────────

function SharedEntryRow({
  entry,
  verification,
  isExpanded,
  onToggle,
}: {
  entry: Entry;
  verification?: VerificationEntry;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-l-2 border-[var(--border)] ml-4 pl-6 pb-4 last:pb-0 relative">
      {/* Timeline dot */}
      <div
        className={`absolute -left-[7px] top-1 h-3 w-3 rounded-full border-2 border-[var(--surface)] ${
          verification?.valid === false
            ? "bg-red-500"
            : verification?.valid === true
              ? "bg-green-500"
              : "bg-[var(--text-tertiary)]"
        }`}
      />

      <button
        onClick={onToggle}
        className="w-full text-left flex items-center gap-3 group"
      >
        <span className="flex-shrink-0 text-[var(--text-tertiary)]">
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
        <span className="font-mono text-xs text-[var(--text-tertiary)] w-8">
          #{entry.index}
        </span>
        <span className="text-sm text-[var(--text-primary)] group-hover:text-pruv-400 transition-colors">
          {entry.action}
        </span>
        <span className="ml-auto text-[10px] font-mono text-[var(--text-tertiary)]">
          {format(new Date(entry.timestamp), "HH:mm:ss")}
        </span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 ml-8 space-y-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
              <HashRow label="x (before)" value={entry.x} />
              <HashRow label="y (after)" value={entry.y} />
              <HashRow label="xy proof" value={entry.xy_proof} />
              <div className="flex items-center gap-2 pt-1">
                <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wider w-20">
                  actor
                </span>
                <span className="font-mono text-xs text-[var(--text-secondary)]">
                  {entry.actor}
                </span>
                {entry.signed && (
                  <span className="rounded-full bg-pruv-500/10 px-2 py-0.5 text-[10px] text-pruv-400">
                    signed
                  </span>
                )}
              </div>
              {verification?.valid === false && verification.reason && (
                <div className="mt-2 rounded-md bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400">
                  {verification.reason}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function HashRow({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wider w-20 flex-shrink-0">
        {label}
      </span>
      <code className="font-mono text-xs text-[var(--text-secondary)] truncate flex-1">
        {value}
      </code>
      <button
        onClick={copy}
        className="flex-shrink-0 text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
      >
        {copied ? (
          <Check size={12} className="text-green-400" />
        ) : (
          <Copy size={12} />
        )}
      </button>
    </div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────

export default function SharedChainPage() {
  const params = useParams();
  const shareId = params.shareId as string;

  const { data, isLoading, error } = useSharedChain(shareId);

  const [clientVerification, setClientVerification] = useState<{
    valid: boolean;
    results: VerificationEntry[];
  } | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const runVerification = useCallback(async () => {
    if (!data?.entries) return;
    setIsVerifying(true);
    try {
      const result = await verifyChainClientSide(data.entries);
      setClientVerification(result);
    } finally {
      setIsVerifying(false);
    }
  }, [data?.entries]);

  const toggleEntry = useCallback((index: number) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  }, []);

  // ─── Loading ────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--surface)] flex items-center justify-center">
        <div className="flex items-center gap-3 text-[var(--text-secondary)]">
          <Loader2 size={20} className="animate-spin" />
          <span className="text-sm">loading shared chain...</span>
        </div>
      </div>
    );
  }

  // ─── Not found ──────────────────────────────────────────────────────────

  if (error || !data) {
    const apiError = error as { status?: number; message?: string } | null;
    const is404 = apiError?.status === 404;

    return (
      <div className="min-h-screen bg-[var(--surface)] flex items-center justify-center">
        <div className="text-center space-y-3 max-w-sm">
          <ShieldX size={48} className="text-[var(--text-tertiary)] mx-auto" />
          <h1 className="text-lg font-semibold text-[var(--text-primary)]">
            {is404 ? "shared chain not found" : "unable to load shared chain"}
          </h1>
          <p className="text-sm text-[var(--text-secondary)]">
            {is404
              ? "this link may have expired or the chain may no longer be shared."
              : "could not reach the verification server. check your connection and try again."}
          </p>
          {!is404 && (
            <button
              onClick={() => window.location.reload()}
              className="mt-2 inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              retry
            </button>
          )}
        </div>
      </div>
    );
  }

  const { chain, entries, verified } = data;
  const firstEntry = entries[0];
  const lastEntry = entries[entries.length - 1];

  return (
    <div className="min-h-screen bg-[var(--surface)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface-secondary)]">
        <div className="mx-auto max-w-3xl px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm font-semibold text-pruv-400">
                pruv
              </span>
              <span className="text-[var(--text-tertiary)]">/</span>
              <span className="text-sm text-[var(--text-secondary)]">
                shared chain
              </span>
            </div>
            <a
              href="https://pruv.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-[var(--text-tertiary)] hover:text-pruv-400 transition-colors"
            >
              what is pruv?
              <ExternalLink size={10} />
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-8 space-y-6">
        {/* Server verification banner */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`flex items-center justify-between rounded-xl border p-5 ${
            verified
              ? "border-green-500/20 bg-green-500/5"
              : "border-red-500/20 bg-red-500/5"
          }`}
        >
          <div className="flex items-center gap-3">
            {verified ? (
              <ShieldCheck size={24} className="text-green-400" />
            ) : (
              <ShieldX size={24} className="text-red-400" />
            )}
            <div>
              <h1
                className={`text-lg font-semibold ${verified ? "text-green-400" : "text-red-400"}`}
              >
                {verified ? "chain verified" : "chain broken"}
              </h1>
              <p className="text-sm text-[var(--text-secondary)]">
                server-side verification at time of retrieval
              </p>
            </div>
          </div>
        </motion.div>

        {/* Chain metadata */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <MetadataCard label="chain name" value={chain.name} />
          <MetadataCard label="entries" value={String(entries.length)} />
          <MetadataCard
            label="created"
            value={format(new Date(chain.created_at), "MMM d, yyyy")}
          />
          <MetadataCard label="type" value={chain.chain_type} />
        </div>

        {/* Hash summary */}
        {firstEntry && lastEntry && (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 space-y-3">
            <h2 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
              chain boundaries
            </h2>
            <HashRow
              label="root x"
              value={firstEntry.x}
            />
            <HashRow
              label="head y"
              value={lastEntry.y}
            />
            <HashRow
              label="root proof"
              value={firstEntry.xy_proof}
            />
            <HashRow
              label="head proof"
              value={lastEntry.xy_proof}
            />
          </div>
        )}

        {/* Client-side verify button */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                independent verification
              </h2>
              <p className="mt-1 text-xs text-[var(--text-tertiary)]">
                re-verify this chain in your browser using Web Crypto API.
                no server trust required.
              </p>
            </div>
            <button
              onClick={runVerification}
              disabled={isVerifying}
              className="flex items-center gap-2 rounded-lg border border-pruv-500/30 bg-pruv-500/10 px-4 py-2 text-sm text-pruv-400 hover:bg-pruv-500/20 transition-colors disabled:opacity-50"
            >
              {isVerifying ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <ShieldCheck size={14} />
              )}
              verify locally
            </button>
          </div>

          {clientVerification && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className={`mt-4 rounded-lg border px-4 py-3 ${
                clientVerification.valid
                  ? "border-green-500/20 bg-green-500/5"
                  : "border-red-500/20 bg-red-500/5"
              }`}
            >
              <div className="flex items-center gap-2">
                {clientVerification.valid ? (
                  <ShieldCheck size={16} className="text-green-400" />
                ) : (
                  <ShieldX size={16} className="text-red-400" />
                )}
                <span
                  className={`text-sm font-medium ${clientVerification.valid ? "text-green-400" : "text-red-400"}`}
                >
                  {clientVerification.valid
                    ? `all ${entries.length} entries verified — chain intact`
                    : `chain broken — ${clientVerification.results.filter((r) => !r.valid).length} invalid entries`}
                </span>
              </div>
            </motion.div>
          )}
        </div>

        {/* Entry timeline */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-pruv-500" />
              <h2 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                entry timeline
              </h2>
              <span className="rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-[10px] font-mono text-[var(--text-tertiary)]">
                {entries.length} entries
              </span>
            </div>
            {entries.length > 0 && (
              <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
                {format(new Date(firstEntry.timestamp), "MMM d")}
                {" — "}
                {format(new Date(lastEntry.timestamp), "MMM d, yyyy")}
              </span>
            )}
          </div>

          <div className="space-y-0">
            {entries.map((entry) => (
              <SharedEntryRow
                key={entry.index}
                entry={entry}
                verification={clientVerification?.results.find(
                  (r) => r.index === entry.index
                )}
                isExpanded={expandedIndex === entry.index}
                onToggle={() => toggleEntry(entry.index)}
              />
            ))}

            {/* Chain origin marker */}
            <div className="flex items-center ml-4 pl-6 pt-2 relative">
              <div className="absolute -left-[7px] top-3 h-3 w-3 rounded-full border-2 border-dashed border-[var(--border-secondary)] bg-[var(--surface)]" />
              <span className="text-xs text-[var(--text-tertiary)]">
                chain origin — GENESIS
              </span>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center py-6 border-t border-[var(--border)]">
          <p className="text-xs text-[var(--text-tertiary)] mb-3">
            cryptographic proof-of-state chains
          </p>
          <a
            href="https://pruv.dev"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-pruv-500/30 bg-pruv-500/10 px-5 py-2.5 text-sm text-pruv-400 hover:bg-pruv-500/20 transition-colors"
          >
            get pruv
            <ExternalLink size={12} />
          </a>
        </div>
      </main>
    </div>
  );
}

function MetadataCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
      <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className="text-sm text-[var(--text-primary)] truncate">{value}</div>
    </div>
  );
}
