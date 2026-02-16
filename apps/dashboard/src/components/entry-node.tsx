"use client";

import { motion } from "framer-motion";
import { Lock, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Entry, EntryValidation } from "@/lib/types";

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
function getActionCategory(action: string): "error" | "success" | "info" | "default" {
  const lower = action.toLowerCase();
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

const categoryColors = {
  error: "bg-red-500 border-red-400 shadow-red-500/30",
  success: "bg-green-500 border-green-400 shadow-green-500/30",
  info: "bg-blue-500 border-blue-400 shadow-blue-500/30",
  default: "bg-[var(--surface-tertiary)] border-[var(--border-secondary)] shadow-none",
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

  // Determine node color: broken > signed > action category
  const nodeColor = isBroken
    ? "bg-red-500 border-red-400 shadow-red-500/30"
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

      {/* Node dot */}
      <div className="relative z-10 flex flex-col items-center mr-4 flex-shrink-0">
        <motion.button
          whileHover={{ scale: 1.15 }}
          whileTap={{ scale: 0.95 }}
          onClick={onToggle}
          className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${nodeColor} shadow-lg transition-colors cursor-pointer`}
        >
          {isBroken ? (
            <AlertTriangle size={16} className="text-white" />
          ) : isSigned ? (
            <Lock size={14} className="text-white" />
          ) : category === "error" ? (
            <AlertTriangle size={14} className="text-white" />
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
          className="w-full text-left rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4 hover:border-pruv-500/40 transition-all duration-200 cursor-pointer"
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
              {category === "error" && !isBroken && (
                <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-400 border border-red-500/20">
                  error
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
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

          {/* Actor and proof */}
          <div className="mt-2 flex items-center gap-4 text-xs text-[var(--text-tertiary)]">
            <span>by {entry.actor}</span>
            <span className="font-mono text-[10px] truncate max-w-48 opacity-60">
              {entry.xy_proof}
            </span>
          </div>
        </button>
      </motion.div>
    </div>
  );
}
