"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { ChainTimeline } from "@/components/chain-timeline";
import { TimeTravel } from "@/components/time-travel";
import { ReplayControls } from "@/components/replay-controls";
import { VerificationBadge } from "@/components/verification-badge";
import { QuickUndo } from "@/components/quick-undo";
import { useChain, useChainVerification } from "@/hooks/use-chains";
import { useEntries, useUndoEntry } from "@/hooks/use-entries";
import type { Entry, EntryValidation } from "@/lib/types";

export default function ChainDetailPage() {
  const params = useParams();
  const chainId = params.id as string;

  const { data: chain, isLoading: chainLoading } = useChain(chainId);
  const { data: entriesData, isLoading: entriesLoading } = useEntries(chainId, { per_page: 100 });
  const {
    data: validations,
    isLoading: isVerifying,
    refetch: runVerification,
  } = useChainVerification(chainId, { enabled: false });

  const undoMutation = useUndoEntry(chainId);

  const entries: Entry[] = entriesData?.data ?? [];
  const [timeTravelIndex, setTimeTravelIndex] = useState<number>(entries.length - 1);

  const displayEntries =
    timeTravelIndex >= 0 && timeTravelIndex < entries.length
      ? entries.slice(0, timeTravelIndex + 1)
      : entries;

  const handleTimeTravelChange = useCallback(
    (index: number) => {
      if (index === -1) {
        // "next" signal from replay
        setTimeTravelIndex((prev) => Math.min(prev + 1, entries.length - 1));
      } else {
        setTimeTravelIndex(index);
      }
    },
    [entries.length]
  );

  const handleVerify = () => {
    runVerification();
  };

  const handleUndo = () => {
    undoMutation.mutate();
  };

  const lastEntry = entries.length > 0 ? entries[entries.length - 1] : undefined;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-64">
        <Header
          title={chain?.name ?? "chain"}
          subtitle={chainLoading ? undefined : `${entries.length} entries`}
          actions={
            <div className="flex items-center gap-3">
              <QuickUndo
                lastEntry={lastEntry}
                onUndo={handleUndo}
                isUndoing={undoMutation.isPending}
              />
              <VerificationBadge
                chainId={chainId}
                validations={validations}
                isVerifying={isVerifying}
                onVerify={handleVerify}
              />
            </div>
          }
        />

        <main className="p-6 space-y-6">
          {/* Chain metadata */}
          {chain && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                    {chain.name}
                  </h2>
                  {chain.description && (
                    <p className="mt-1 text-sm text-[var(--text-tertiary)]">
                      {chain.description}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
                    chain id
                  </div>
                  <code className="text-xs font-mono text-[var(--text-secondary)]">
                    {chainId}
                  </code>
                </div>
              </div>

              {chain.tags.length > 0 && (
                <div className="mt-3 flex items-center gap-1.5">
                  {chain.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-[var(--surface-tertiary)] border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--text-tertiary)]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Time travel + replay controls */}
          {entries.length > 1 && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <TimeTravel
                entries={entries}
                currentIndex={timeTravelIndex}
                onIndexChange={handleTimeTravelChange}
              />
              <div className="flex items-end">
                <ReplayControls
                  totalEntries={entries.length}
                  currentIndex={timeTravelIndex}
                  onIndexChange={handleTimeTravelChange}
                />
              </div>
            </div>
          )}

          {/* The vertical chain timeline — core visualization */}
          <ChainTimeline
            entries={displayEntries}
            validations={validations}
            chainId={chainId}
            isLoading={entriesLoading}
          />
        </main>
      </div>
    </div>
  );
}
