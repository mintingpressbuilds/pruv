"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Filter } from "lucide-react";
import { EntryNode } from "./entry-node";
import { EntryDetail } from "./entry-detail";
import type { Entry, EntryValidation } from "@/lib/types";

interface ChainTimelineProps {
  entries: Entry[];
  validations?: EntryValidation[];
  chainId: string;
  isLoading?: boolean;
  actionFilter?: string;
  onActionFilterChange?: (filter: string) => void;
  actionTypes?: string[];
}

export function ChainTimeline({
  entries,
  validations = [],
  chainId,
  isLoading = false,
  actionFilter = "",
  onActionFilterChange,
  actionTypes = [],
}: ChainTimelineProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const toggleEntry = useCallback(
    (index: number) => {
      setExpandedIndex((prev) => (prev === index ? null : index));
    },
    []
  );

  const getValidation = (index: number): EntryValidation | undefined => {
    return validations.find((v) => v.index === index);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-start">
            <div className="relative z-10 mr-4 flex-shrink-0">
              <div className="h-10 w-10 rounded-full bg-[var(--surface-tertiary)] animate-pulse" />
            </div>
            <div className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
              <div className="h-4 w-48 rounded bg-[var(--surface-tertiary)] animate-pulse" />
              <div className="mt-2 h-3 w-32 rounded bg-[var(--surface-tertiary)] animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--surface-secondary)] border border-[var(--border)] mb-4">
          <div className="h-3 w-3 rounded-full bg-[var(--text-tertiary)]" />
        </div>
        <p className="text-sm text-[var(--text-secondary)]">
          {actionFilter ? "no entries match this filter" : "no entries in this chain yet"}
        </p>
        <p className="mt-1 text-xs text-[var(--text-tertiary)]">
          {actionFilter ? (
            <button
              onClick={() => onActionFilterChange?.("")}
              className="text-pruv-400 hover:text-pruv-300"
            >
              clear filter
            </button>
          ) : (
            "entries will appear here as state transitions are recorded"
          )}
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Timeline header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-pruv-500 animate-pulse" />
          <span className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
            chain timeline
          </span>
          <span className="rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-[10px] font-mono text-[var(--text-tertiary)]">
            {entries.length} entries
          </span>

          {/* Action type filter */}
          {actionTypes.length > 1 && onActionFilterChange && (
            <div className="flex items-center gap-1.5 ml-2">
              <Filter size={12} className="text-[var(--text-tertiary)]" />
              <select
                value={actionFilter}
                onChange={(e) => onActionFilterChange(e.target.value)}
                className="rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] px-2 py-1 text-[10px] text-[var(--text-secondary)] focus:border-pruv-500/50 focus:outline-none"
              >
                <option value="">all actions</option>
                {actionTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 text-[10px] text-[var(--text-tertiary)]">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            complete
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-blue-500" />
            start
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-red-500" />
            error
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-pruv-500" />
            signed
          </span>
        </div>
      </div>

      {/* Timeline entries */}
      <div className="relative">
        <AnimatePresence mode="sync">
          {entries.map((entry, i) => (
            <div key={entry.index}>
              <EntryNode
                entry={entry}
                validation={getValidation(entry.index)}
                isExpanded={expandedIndex === entry.index}
                onToggle={() => toggleEntry(entry.index)}
                isFirst={i === 0}
                isLast={i === entries.length - 1}
                index={i}
              />
              {expandedIndex === entry.index && (
                <motion.div
                  key={`detail-${entry.index}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <EntryDetail
                    entry={entry}
                    validation={getValidation(entry.index)}
                    chainId={chainId}
                  />
                </motion.div>
              )}
            </div>
          ))}
        </AnimatePresence>

        {/* Chain origin marker */}
        <div className="flex items-center ml-1 mt-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-dashed border-[var(--border-secondary)] bg-[var(--surface)]">
            <span className="text-[10px] text-[var(--text-tertiary)]">0</span>
          </div>
          <span className="ml-4 text-xs text-[var(--text-tertiary)]">
            chain origin
          </span>
        </div>
      </div>
    </div>
  );
}
