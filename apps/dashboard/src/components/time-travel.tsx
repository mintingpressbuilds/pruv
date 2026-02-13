"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Clock, SkipBack, SkipForward } from "lucide-react";
import type { Entry } from "@/lib/types";

interface TimeTravelProps {
  entries: Entry[];
  currentIndex: number;
  onIndexChange: (index: number) => void;
}

export function TimeTravel({
  entries,
  currentIndex,
  onIndexChange,
}: TimeTravelProps) {
  const [isDragging, setIsDragging] = useState(false);
  const maxIndex = entries.length - 1;

  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onIndexChange(Number(e.target.value));
    },
    [onIndexChange]
  );

  const goToPrev = useCallback(() => {
    if (currentIndex > 0) onIndexChange(currentIndex - 1);
  }, [currentIndex, onIndexChange]);

  const goToNext = useCallback(() => {
    if (currentIndex < maxIndex) onIndexChange(currentIndex + 1);
  }, [currentIndex, maxIndex, onIndexChange]);

  const currentEntry = entries[currentIndex];

  if (entries.length === 0) return null;

  const progress = maxIndex > 0 ? (currentIndex / maxIndex) * 100 : 100;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
      <div className="flex items-center gap-2 mb-3">
        <Clock size={14} className="text-pruv-400" />
        <span className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
          time travel
        </span>
        <span className="ml-auto rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-[10px] font-mono text-pruv-400">
          entry {currentIndex} of {maxIndex}
        </span>
      </div>

      {/* Slider */}
      <div className="relative mb-3">
        <div className="h-1.5 rounded-full bg-[var(--surface-tertiary)] overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-pruv-600 to-pruv-400"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.15 }}
          />
        </div>
        <input
          type="range"
          min={0}
          max={maxIndex}
          value={currentIndex}
          onChange={handleSliderChange}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={() => setIsDragging(false)}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
        />

        {/* Tick marks for entries */}
        <div className="absolute top-0 left-0 right-0 flex justify-between pointer-events-none">
          {entries.length <= 20 &&
            entries.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 w-1 rounded-full ${
                  i <= currentIndex ? "bg-pruv-300" : "bg-[var(--border)]"
                }`}
              />
            ))}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={goToPrev}
            disabled={currentIndex === 0}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <SkipBack size={14} />
          </button>
          <button
            onClick={goToNext}
            disabled={currentIndex === maxIndex}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <SkipForward size={14} />
          </button>
        </div>

        {currentEntry && (
          <div className="text-xs text-[var(--text-tertiary)]">
            <span className="text-[var(--text-secondary)]">
              {currentEntry.action}
            </span>
            {" by "}
            {currentEntry.actor}
          </div>
        )}
      </div>

      {isDragging && currentEntry && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 rounded-lg border border-pruv-500/20 bg-pruv-500/5 p-3"
        >
          <div className="text-xs text-[var(--text-secondary)]">
            <span className="font-mono text-pruv-400">
              #{currentEntry.index}
            </span>{" "}
            {currentEntry.action}
          </div>
          <div className="mt-1 font-mono text-[10px] text-[var(--text-tertiary)] truncate">
            {currentEntry.xy_proof}
          </div>
        </motion.div>
      )}
    </div>
  );
}
