"use client";

import { motion } from "framer-motion";
import { Lock, AlertTriangle, ChevronDown, ChevronUp, ArrowRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Entry, EntryValidation, XYProofData } from "@/lib/types";

interface EntryNodeProps {
  entry: Entry;
  validation?: EntryValidation;
  isExpanded: boolean;
  onToggle: () => void;
  isFirst: boolean;
  isLast: boolean;
  index: number;
}

/**
 * Determine the action category from the entry action string.
 * Used for color-coding the timeline dots.
 */
function getActionCategory(action: string): "error" | "success" | "info" | "payment" | "default" {
  const lower = action.toLowerCase();
  if (lower.startsWith("payment.")) {
    return "payment";
  }
  if (lower.includes(".error") || lower.includes("error") || lower.includes("fail")) {
    return "error";
  }
  if (lower.includes(".complete") || lower.includes("success") || lower.includes("finish")) {
    return "success";
  }
  if (lower.includes(".start") || lower.includes("kickoff") || lower.includes("begin")) {
    return "info";
  }
  return "default";
}

/**
 * Determine the payment sub-type for color coding.
 */
function getPaymentType(action: string): "deposit" | "withdraw" | "transfer" {
  const lower = action.toLowerCase();
  if (lower.includes("deposit")) return "deposit";
  if (lower.includes("withdraw")) return "withdraw";
  return "transfer";
}

/**
 * Extract xy_proof data from entry metadata.
 * Checks both metadata.xy_proof (standard API) and metadata.data.xy_proof (Agent path).
 */
export function getXYProof(entry: Entry): XYProofData | null {
  const meta = entry.metadata;
  if (!meta) return null;

  const direct = meta.xy_proof as XYProofData | undefined;
  if (direct && typeof direct === "object" && "xy" in direct) return direct;

  const nested = meta.data as Record<string, unknown> | undefined;
  if (nested && typeof nested === "object") {
    const proof = nested.xy_proof as XYProofData | undefined;
    if (proof && typeof proof === "object" && "xy" in proof) return proof;
  }

  return null;
}

/**
 * Check if an entry is a payment entry.
 */
export function isPaymentEntry(entry: Entry): boolean {
  return entry.action.toLowerCase().startsWith("payment.") || getXYProof(entry) !== null;
}

/**
 * Get payment data from entry metadata (from Agent path).
 */
function getPaymentData(entry: Entry): Record<string, unknown> | null {
  const meta = entry.metadata;
  if (!meta) return null;
  const data = meta.data as Record<string, unknown> | undefined;
  if (data && typeof data === "object") return data;
  return null;
}

const categoryColors = {
  error: "bg-red-500 border-red-400 shadow-red-500/30",
  success: "bg-green-500 border-green-400 shadow-green-500/30",
  info: "bg-blue-500 border-blue-400 shadow-blue-500/30",
  payment: "bg-emerald-500 border-emerald-400 shadow-emerald-500/30",
  default: "bg-[var(--surface-tertiary)] border-[var(--border-secondary)] shadow-none",
} as const;

const paymentTypeColors = {
  deposit: "bg-green-500 border-green-400 shadow-green-500/30",
  withdraw: "bg-red-500 border-red-400 shadow-red-500/30",
  transfer: "bg-blue-500 border-blue-400 shadow-blue-500/30",
} as const;

export function EntryNode({
  entry,
  validation,
  isExpanded,
  onToggle,
  isFirst,
  isLast,
  index,
}: EntryNodeProps) {
  const isBroken = validation && !validation.valid;
  const isSigned = entry.signed;
  const category = getActionCategory(entry.action);
  const isPayment = category === "payment" || isPaymentEntry(entry);
  const paymentType = isPayment ? getPaymentType(entry.action) : null;
  const xyProof = isPayment ? getXYProof(entry) : null;
  const paymentData = isPayment ? getPaymentData(entry) : null;

  // Payment amount, sender, recipient from proof or metadata.data
  const amount = xyProof?.amount ?? (paymentData?.amount as number | undefined);
  const sender = xyProof?.sender ?? (paymentData?.sender as string | undefined);
  const recipient = xyProof?.recipient ?? (paymentData?.recipient as string | undefined);
  const source = paymentData?.source as string | undefined;
  const reference = paymentData?.reference as string | undefined;

  // Determine node color: broken > payment type > signed > action category
  const nodeColor = isBroken
    ? "bg-red-500 border-red-400 shadow-red-500/30"
    : isPayment && paymentType
      ? paymentTypeColors[paymentType]
      : isSigned
        ? "bg-pruv-500 border-pruv-400 shadow-pruv-500/30"
        : categoryColors[category];

  const lineColor = isBroken
    ? "bg-red-500/40"
    : "bg-gradient-to-b from-pruv-500/60 to-pruv-600/60";

  return (
    <div className="relative flex items-start">
      {/* Vertical line segment */}
      {!isLast && (
        <div
          className={`absolute left-[19px] top-10 bottom-0 w-0.5 ${lineColor}`}
          style={{ minHeight: isExpanded ? "100%" : "48px" }}
        />
      )}

      {/* Node dot — diamond for payments, circle for others */}
      <div className="relative z-10 flex flex-col items-center mr-4 flex-shrink-0">
        <motion.button
          whileHover={{ scale: 1.15 }}
          whileTap={{ scale: 0.95 }}
          onClick={onToggle}
          className={`flex h-10 w-10 items-center justify-center ${
            isPayment ? "rotate-45 rounded-md" : "rounded-full"
          } border-2 ${nodeColor} shadow-lg transition-colors cursor-pointer`}
        >
          {isBroken ? (
            <AlertTriangle size={16} className={`text-white ${isPayment ? "-rotate-45" : ""}`} />
          ) : isSigned ? (
            <Lock size={14} className={`text-white ${isPayment ? "-rotate-45" : ""}`} />
          ) : category === "error" ? (
            <AlertTriangle size={14} className={`text-white ${isPayment ? "-rotate-45" : ""}`} />
          ) : isPayment ? (
            <span className="-rotate-45 text-xs font-bold text-white">
              $
            </span>
          ) : (
            <span className="text-xs font-bold text-[var(--text-primary)]">
              {entry.index}
            </span>
          )}
        </motion.button>
      </div>

      {/* Entry card */}
      <motion.div
        layout
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05, duration: 0.2 }}
        className="flex-1 mb-4"
      >
        <button
          onClick={onToggle}
          className={`w-full text-left rounded-xl border ${
            isPayment
              ? "border-emerald-500/20 bg-emerald-500/5 hover:border-emerald-500/40"
              : "border-[var(--border)] bg-[var(--surface-secondary)] hover:border-pruv-500/40"
          } p-4 transition-all duration-200 cursor-pointer`}
        >
          {/* Entry header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono font-bold text-pruv-400">
                #{entry.index}
              </span>
              <span className="text-sm font-medium text-[var(--text-primary)]">
                {entry.action}
              </span>
              {isBroken && (
                <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-400 border border-red-500/20">
                  <AlertTriangle size={10} />
                  broken link
                </span>
              )}
              {isSigned && (
                <span className="inline-flex items-center gap-1 rounded-full bg-pruv-500/10 px-2 py-0.5 text-[10px] font-medium text-pruv-400 border border-pruv-500/20">
                  <Lock size={10} />
                  signed
                </span>
              )}
              {isPayment && xyProof?.valid && (
                <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 px-2 py-0.5 text-[10px] font-medium text-green-400 border border-green-500/20">
                  ✓ verified
                </span>
              )}
              {isPayment && xyProof && !xyProof.valid && (
                <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-400 border border-red-500/20">
                  ✗ invalid
                </span>
              )}
              {category === "error" && !isBroken && !isPayment && (
                <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-400 border border-red-500/20">
                  error
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {/* Payment amount */}
              {isPayment && amount !== undefined && (
                <span className={`text-sm font-mono font-semibold ${
                  paymentType === "deposit"
                    ? "text-green-400"
                    : paymentType === "withdraw"
                      ? "text-red-400"
                      : "text-blue-400"
                }`}>
                  {paymentType === "deposit" ? "+" : paymentType === "withdraw" ? "-" : ""}${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              )}
              <span className="text-xs text-[var(--text-tertiary)]">
                {formatDistanceToNow(new Date(entry.timestamp), {
                  addSuffix: true,
                })}
              </span>
              {isExpanded ? (
                <ChevronUp size={16} className="text-[var(--text-tertiary)]" />
              ) : (
                <ChevronDown
                  size={16}
                  className="text-[var(--text-tertiary)]"
                />
              )}
            </div>
          </div>

          {/* Payment details row */}
          {isPayment && (sender || recipient) && (
            <div className="mt-2 flex items-center gap-3 text-xs text-[var(--text-secondary)]">
              {sender && recipient && (
                <span className="inline-flex items-center gap-1.5 font-medium">
                  {sender}
                  <ArrowRight size={10} className="text-[var(--text-tertiary)]" />
                  {recipient}
                </span>
              )}
              {source && (
                <span className="text-[var(--text-tertiary)]">
                  via {source}
                </span>
              )}
              {reference && (
                <span className="font-mono text-[10px] text-[var(--text-tertiary)] truncate max-w-32">
                  ref: {reference}
                </span>
              )}
            </div>
          )}

          {/* Actor and proof */}
          <div className="mt-2 flex items-center gap-4 text-xs text-[var(--text-tertiary)]">
            <span>by {entry.actor}</span>
            <span className="font-mono text-[10px] truncate max-w-48 opacity-60">
              {entry.xy_proof}
            </span>
            {isPayment && xyProof && (
              <span className="font-mono text-[10px] opacity-60">
                {xyProof.xy.slice(0, 8)}...
              </span>
            )}
          </div>
        </button>
      </motion.div>
    </div>
  );
}
