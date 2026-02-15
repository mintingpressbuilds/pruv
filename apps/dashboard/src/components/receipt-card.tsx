"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ShieldX, Clock, AlertCircle, FileCheck } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Receipt } from "@/lib/types";
import { PruvIcon } from "@/components/icons/pruv-icon";

interface ReceiptCardProps {
  receipt: Receipt;
  index?: number;
}

function PruvStatusIcon({ size, className }: { size?: number; className?: string }) {
  return <PruvIcon size={size} className={className} />;
}

const statusConfig = {
  verified: {
    icon: PruvStatusIcon,
    color: "text-green-400",
    bg: "bg-green-500/10 border-green-500/20",
    label: "verified",
  },
  failed: {
    icon: ShieldX,
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
    label: "failed",
  },
  pending: {
    icon: Clock,
    color: "text-yellow-400",
    bg: "bg-yellow-500/10 border-yellow-500/20",
    label: "pending",
  },
  expired: {
    icon: AlertCircle,
    color: "text-[var(--text-tertiary)]",
    bg: "bg-[var(--surface-tertiary)] border-[var(--border)]",
    label: "expired",
  },
};

export function ReceiptCard({ receipt, index = 0 }: ReceiptCardProps) {
  const status = statusConfig[receipt.status];
  const StatusIcon = status.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Link
        href={`/receipts/${receipt.id}`}
        className="group block rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 hover:border-pruv-500/40 transition-all duration-200"
      >
        <div className="flex items-start justify-between">
          {/* Receipt info */}
          <div className="flex items-start gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-lg border ${status.bg}`}
            >
              <StatusIcon size={18} className={status.color} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-[var(--text-primary)] group-hover:text-pruv-400 transition-colors">
                  {receipt.chain_name}
                </span>
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${status.bg} ${status.color}`}
                >
                  {status.label}
                </span>
              </div>
              <div className="mt-1 text-xs text-[var(--text-tertiary)]">
                entries {receipt.entry_range.start}–{receipt.entry_range.end}
              </div>
            </div>
          </div>

          {/* Timestamp */}
          <span className="text-xs text-[var(--text-tertiary)]">
            {formatDistanceToNow(new Date(receipt.created_at), {
              addSuffix: true,
            })}
          </span>
        </div>

        {/* Summary */}
        <div className="mt-3 text-xs text-[var(--text-secondary)]">
          {receipt.verification_result.summary}
        </div>

        {/* Stats row */}
        <div className="mt-3 flex items-center gap-4 text-[10px] text-[var(--text-tertiary)]">
          <span className="flex items-center gap-1">
            <FileCheck size={10} />
            {receipt.verification_result.entries_checked} checked
          </span>
          {receipt.verification_result.broken_links.length > 0 && (
            <span className="text-red-400">
              {receipt.verification_result.broken_links.length} broken
            </span>
          )}
          <span className="font-mono truncate max-w-32">
            {receipt.id.slice(0, 12)}...
          </span>
        </div>
      </Link>
    </motion.div>
  );
}
