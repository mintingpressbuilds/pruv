"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Undo2, AlertTriangle, Loader2 } from "lucide-react";
import { StateDiff } from "./state-diff";
import type { Entry } from "@/lib/types";

interface QuickUndoProps {
  lastEntry?: Entry;
  onUndo: () => void;
  isUndoing?: boolean;
}

export function QuickUndo({ lastEntry, onUndo, isUndoing }: QuickUndoProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  if (!lastEntry) return null;

  const handleUndo = () => {
    if (!confirmed) {
      setConfirmed(true);
      return;
    }
    onUndo();
    setConfirmed(false);
    setShowPreview(false);
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onMouseEnter={() => setShowPreview(true)}
          onMouseLeave={() => {
            if (!confirmed) {
              setShowPreview(false);
            }
          }}
          onClick={handleUndo}
          disabled={isUndoing}
          className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-all ${
            confirmed
              ? "border-red-500/30 bg-red-500/10 text-red-400"
              : "border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-yellow-500/40"
          } disabled:opacity-50`}
        >
          {isUndoing ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Undo2 size={14} />
          )}
          {confirmed ? (
            <span className="flex items-center gap-1">
              <AlertTriangle size={12} />
              confirm undo
            </span>
          ) : (
            "quick undo"
          )}
        </motion.button>

        {confirmed && (
          <button
            onClick={() => {
              setConfirmed(false);
              setShowPreview(false);
            }}
            className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
          >
            cancel
          </button>
        )}
      </div>

      {/* Preview dropdown */}
      <AnimatePresence>
        {showPreview && (
          <motion.div
            initial={{ opacity: 0, y: -5, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -5, scale: 0.97 }}
            className="absolute top-full mt-2 left-0 w-96 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xl p-4 z-50"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                undo preview — entry #{lastEntry.index}
              </h4>
              <span className="text-[10px] text-[var(--text-tertiary)]">
                {lastEntry.action}
              </span>
            </div>

            <p className="text-xs text-[var(--text-tertiary)] mb-3">
              this will revert the last state transition, restoring y back to x:
            </p>

            <StateDiff x={lastEntry.y} y={lastEntry.x} compact />

            <p className="mt-3 text-[10px] text-[var(--text-tertiary)]">
              {confirmed
                ? "click again to confirm the undo operation"
                : "click the button to initiate undo"}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
