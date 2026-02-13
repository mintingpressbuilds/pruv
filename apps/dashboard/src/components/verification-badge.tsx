"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, ShieldX, Loader2, Play } from "lucide-react";
import type { EntryValidation } from "@/lib/types";

interface VerificationBadgeProps {
  chainId: string;
  validations?: EntryValidation[];
  isVerifying?: boolean;
  onVerify?: () => void;
}

export function VerificationBadge({
  validations,
  isVerifying = false,
  onVerify,
}: VerificationBadgeProps) {
  const [showDetails, setShowDetails] = useState(false);

  const hasValidations = validations && validations.length > 0;
  const allValid = hasValidations && validations.every((v) => v.valid);
  const brokenCount = hasValidations
    ? validations.filter((v) => !v.valid).length
    : 0;

  return (
    <div className="relative">
      <AnimatePresence mode="wait">
        {isVerifying ? (
          <motion.div
            key="verifying"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="verify-pulse flex items-center gap-2 rounded-full border border-pruv-500/30 bg-pruv-500/10 px-4 py-2"
          >
            <Loader2 size={16} className="text-pruv-400 animate-spin" />
            <span className="text-sm font-medium text-pruv-400">
              verifying chain...
            </span>
          </motion.div>
        ) : hasValidations ? (
          <motion.button
            key="result"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            whileHover={{ scale: 1.02 }}
            onClick={() => setShowDetails(!showDetails)}
            className={`flex items-center gap-2 rounded-full border px-4 py-2 transition-colors cursor-pointer ${
              allValid
                ? "border-green-500/30 bg-green-500/10 text-green-400 hover:bg-green-500/15"
                : "border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/15"
            }`}
          >
            {allValid ? (
              <>
                <ShieldCheck size={16} />
                <span className="text-sm font-medium">
                  chain verified ({validations.length} entries)
                </span>
              </>
            ) : (
              <>
                <ShieldX size={16} />
                <span className="text-sm font-medium">
                  {brokenCount} broken link{brokenCount !== 1 ? "s" : ""} found
                </span>
              </>
            )}
          </motion.button>
        ) : (
          <motion.button
            key="trigger"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onVerify}
            className="flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-pruv-500/40 transition-colors cursor-pointer"
          >
            <Play size={14} />
            <span className="text-sm font-medium">verify chain</span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Details dropdown */}
      <AnimatePresence>
        {showDetails && hasValidations && (
          <motion.div
            initial={{ opacity: 0, y: -5, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -5, scale: 0.97 }}
            className="absolute top-full mt-2 right-0 w-72 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xl p-4 z-50"
          >
            <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
              verification details
            </h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {validations.map((v) => (
                <div
                  key={v.index}
                  className={`flex items-center justify-between rounded-lg px-3 py-2 text-xs ${
                    v.valid
                      ? "bg-green-500/5 text-green-400"
                      : "bg-red-500/5 text-red-400"
                  }`}
                >
                  <span className="font-mono">entry #{v.index}</span>
                  <div className="flex items-center gap-2">
                    {v.x_matches_prev_y ? (
                      <span className="text-[10px]">x=prev.y</span>
                    ) : (
                      <span className="text-[10px] text-red-400">
                        x!=prev.y
                      </span>
                    )}
                    {v.proof_valid ? (
                      <span className="text-[10px]">proof ok</span>
                    ) : (
                      <span className="text-[10px] text-red-400">
                        bad proof
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
