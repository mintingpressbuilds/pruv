"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldX,
  Download,
  Copy,
  Check,
  ExternalLink,
  Brain,
  Clock,
  Loader2,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import type { Receipt, ThinkingStep } from "@/lib/types";
import { PruvIcon } from "@/components/icons/pruv-icon";
import { PruvBadge } from "@/components/icons/pruv-badge";

interface ReceiptDetailProps {
  receipt: Receipt;
  onExportPdf?: () => void;
  isExporting?: boolean;
}

function ThinkingPhaseView({ steps }: { steps: ThinkingStep[] }) {
  return (
    <div className="space-y-2">
      {steps.map((step, i) => (
        <motion.div
          key={step.index}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1 }}
          className="flex items-center gap-3 rounded-lg bg-[var(--surface-secondary)] px-4 py-3 border border-[var(--border)]"
        >
          <div className="flex-shrink-0">
            {step.status === "completed" ? (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500/10">
                <Check size={12} className="text-green-400" />
              </div>
            ) : step.status === "in_progress" ? (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-pruv-500/10">
                <Loader2 size={12} className="text-pruv-400 animate-spin" />
              </div>
            ) : step.status === "failed" ? (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-500/10">
                <ShieldX size={12} className="text-red-400" />
              </div>
            ) : (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--surface-tertiary)]">
                <Clock size={12} className="text-[var(--text-tertiary)]" />
              </div>
            )}
          </div>
          <div className="flex-1">
            <p className="text-sm text-[var(--text-primary)]">
              {step.description}
            </p>
          </div>
          {step.duration_ms !== undefined && (
            <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
              {step.duration_ms}ms
            </span>
          )}
        </motion.div>
      ))}
    </div>
  );
}

export function ReceiptDetailView({
  receipt,
  onExportPdf,
  isExporting,
}: ReceiptDetailProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showThinking, setShowThinking] = useState(false);

  const isVerified = receipt.status === "verified";

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Status banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`flex items-center justify-between rounded-xl border p-5 ${
          isVerified
            ? "border-green-500/20 bg-green-500/5"
            : "border-red-500/20 bg-red-500/5"
        }`}
      >
        <div className="flex items-center gap-3">
          {isVerified ? (
            <PruvIcon size={24} className="text-green-400" />
          ) : (
            <ShieldX size={24} className="text-red-400" />
          )}
          <div>
            <h3
              className={`text-lg font-semibold ${isVerified ? "text-green-400" : "text-red-400"}`}
            >
              {isVerified ? "chain verified" : "verification failed"}
            </h3>
            <p className="text-sm text-[var(--text-secondary)]">
              {receipt.verification_result.summary}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onExportPdf}
            disabled={isExporting}
            className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors disabled:opacity-50"
          >
            {isExporting ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Download size={14} />
            )}
            export pdf
          </button>
        </div>
      </motion.div>

      {/* Receipt metadata */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
            receipt id
          </div>
          <div className="flex items-center gap-2">
            <code className="text-sm font-mono text-[var(--text-primary)] truncate">
              {receipt.id}
            </code>
            <button
              onClick={() => copyToClipboard(receipt.id, "id")}
              className="flex-shrink-0 text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
            >
              {copiedField === "id" ? (
                <Check size={12} className="text-green-400" />
              ) : (
                <Copy size={12} />
              )}
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
            chain
          </div>
          <a
            href={`/chains/${receipt.chain_id}`}
            className="flex items-center gap-1.5 text-sm text-pruv-400 hover:text-pruv-300"
          >
            {receipt.chain_name}
            <ExternalLink size={10} />
          </a>
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
            entries checked
          </div>
          <div className="text-sm text-[var(--text-primary)]">
            {receipt.verification_result.entries_checked} entries (
            {receipt.entry_range.start}–{receipt.entry_range.end})
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
            issued
          </div>
          <div className="text-sm text-[var(--text-primary)]">
            {format(new Date(receipt.created_at), "MMM d, yyyy HH:mm")}
          </div>
          <div className="text-xs text-[var(--text-tertiary)]">
            {formatDistanceToNow(new Date(receipt.created_at), {
              addSuffix: true,
            })}
          </div>
        </div>
      </div>

      {/* Verification stats */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
        <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-4">
          verification results
        </h4>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center rounded-lg bg-[var(--surface)] p-4 border border-[var(--border)]">
            <div className="text-2xl font-bold text-[var(--text-primary)]">
              {receipt.verification_result.entries_checked}
            </div>
            <div className="mt-1 text-xs text-[var(--text-tertiary)]">
              entries checked
            </div>
          </div>
          <div className="text-center rounded-lg bg-[var(--surface)] p-4 border border-[var(--border)]">
            <div
              className={`text-2xl font-bold ${receipt.verification_result.broken_links.length > 0 ? "text-red-400" : "text-green-400"}`}
            >
              {receipt.verification_result.broken_links.length}
            </div>
            <div className="mt-1 text-xs text-[var(--text-tertiary)]">
              broken links
            </div>
          </div>
          <div className="text-center rounded-lg bg-[var(--surface)] p-4 border border-[var(--border)]">
            <div
              className={`text-2xl font-bold ${receipt.verification_result.unsigned_entries.length > 0 ? "text-yellow-400" : "text-green-400"}`}
            >
              {receipt.verification_result.unsigned_entries.length}
            </div>
            <div className="mt-1 text-xs text-[var(--text-tertiary)]">
              unsigned entries
            </div>
          </div>
        </div>
      </div>

      {/* Thinking phase */}
      {receipt.thinking_phase && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
          <button
            onClick={() => setShowThinking(!showThinking)}
            className="flex w-full items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <Brain size={16} className="text-pruv-400" />
              <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                thinking phase
              </h4>
              <span className="rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-[10px] text-[var(--text-tertiary)]">
                {receipt.thinking_phase.steps.length} steps
              </span>
            </div>
          </button>
          <AnimatePresence>
            {showThinking && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="mt-4 overflow-hidden"
              >
                <ThinkingPhaseView steps={receipt.thinking_phase.steps} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Embeddable badge */}
      {receipt.badge_url && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
          <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
            embeddable badge
          </h4>
          <div className="flex items-center gap-4">
            <PruvBadge height={32} />
            <div className="flex-1">
              <code className="block rounded-md bg-[var(--surface)] px-3 py-2 font-mono text-xs text-[var(--text-secondary)] border border-[var(--border)] truncate">
                {`<img src="${receipt.badge_url}" alt="pruv verified" />`}
              </code>
            </div>
            <button
              onClick={() =>
                copyToClipboard(
                  `<img src="${receipt.badge_url}" alt="pruv verified" />`,
                  "badge"
                )
              }
              className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              {copiedField === "badge" ? (
                <Check size={14} className="text-green-400" />
              ) : (
                <Copy size={14} />
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
