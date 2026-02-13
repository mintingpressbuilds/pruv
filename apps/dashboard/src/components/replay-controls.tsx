"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { Play, Pause, RotateCcw, Gauge } from "lucide-react";

interface ReplayControlsProps {
  totalEntries: number;
  currentIndex: number;
  onIndexChange: (index: number) => void;
  onPlayStateChange?: (playing: boolean) => void;
}

const SPEED_OPTIONS = [
  { label: "0.5x", value: 2000 },
  { label: "1x", value: 1000 },
  { label: "2x", value: 500 },
  { label: "4x", value: 250 },
];

export function ReplayControls({
  totalEntries,
  currentIndex,
  onIndexChange,
  onPlayStateChange,
}: ReplayControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedIndex, setSpeedIndex] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const speed = SPEED_OPTIONS[speedIndex];

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPlaying(false);
    onPlayStateChange?.(false);
  }, [onPlayStateChange]);

  const play = useCallback(() => {
    if (currentIndex >= totalEntries - 1) {
      onIndexChange(0);
    }

    setIsPlaying(true);
    onPlayStateChange?.(true);

    intervalRef.current = setInterval(() => {
      onIndexChange(-1); // signal "next"
    }, speed.value);
  }, [currentIndex, totalEntries, speed.value, onIndexChange, onPlayStateChange]);

  // Handle the "next" signal
  useEffect(() => {
    if (!isPlaying) return;

    if (currentIndex >= totalEntries - 1) {
      stop();
    }
  }, [currentIndex, totalEntries, isPlaying, stop]);

  // Update interval when speed changes
  useEffect(() => {
    if (isPlaying) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        onIndexChange(-1);
      }, speed.value);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [speed.value, isPlaying, onIndexChange]);

  const togglePlay = () => {
    if (isPlaying) {
      stop();
    } else {
      play();
    }
  };

  const reset = () => {
    stop();
    onIndexChange(0);
  };

  const cycleSpeed = () => {
    setSpeedIndex((prev) => (prev + 1) % SPEED_OPTIONS.length);
  };

  return (
    <div className="flex items-center gap-2">
      {/* Play/Pause */}
      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={togglePlay}
        className={`flex h-9 w-9 items-center justify-center rounded-lg border transition-colors ${
          isPlaying
            ? "border-pruv-500 bg-pruv-500/10 text-pruv-400"
            : "border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
        }`}
      >
        {isPlaying ? <Pause size={14} /> : <Play size={14} />}
      </motion.button>

      {/* Reset */}
      <button
        onClick={reset}
        className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
      >
        <RotateCcw size={14} />
      </button>

      {/* Speed */}
      <button
        onClick={cycleSpeed}
        className="flex h-9 items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
      >
        <Gauge size={12} />
        {speed.label}
      </button>

      {/* Progress indicator */}
      {isPlaying && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]"
        >
          <div className="h-2 w-2 rounded-full bg-pruv-500 animate-pulse" />
          replaying...
        </motion.div>
      )}
    </div>
  );
}
