"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Save,
  RotateCcw,
  Loader2,
  Share2,
  Copy,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { ChainTimeline } from "@/components/chain-timeline";
import { TimeTravel } from "@/components/time-travel";
import { ReplayControls } from "@/components/replay-controls";
import { VerificationBadge } from "@/components/verification-badge";
import { QuickUndo } from "@/components/quick-undo";
import { useChain, useChainVerification } from "@/hooks/use-chains";
import { useEntries, useUndoEntry } from "@/hooks/use-entries";
import {
  useCheckpoints,
  useCreateCheckpoint,
  useCheckpointPreview,
  useRestoreCheckpoint,
} from "@/hooks/use-checkpoints";
import { chains } from "@/lib/api";
import type { Entry } from "@/lib/types";

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

  // Checkpoint state
  const { data: checkpointList = [] } = useCheckpoints(chainId);
  const createCheckpointMutation = useCreateCheckpoint(chainId);
  const restoreCheckpointMutation = useRestoreCheckpoint(chainId);
  const [showCheckpoints, setShowCheckpoints] = useState(false);
  const [checkpointName, setCheckpointName] = useState("");
  const [previewId, setPreviewId] = useState<string | null>(null);
  const { data: previewData } = useCheckpointPreview(
    chainId,
    previewId ?? "",
    { enabled: !!previewId }
  );

  // Share state
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copiedShare, setCopiedShare] = useState(false);

  const entries: Entry[] = entriesData?.data ?? [];
  const [timeTravelIndex, setTimeTravelIndex] = useState<number>(entries.length - 1);

  const displayEntries =
    timeTravelIndex >= 0 && timeTravelIndex < entries.length
      ? entries.slice(0, timeTravelIndex + 1)
      : entries;

  const handleTimeTravelChange = useCallback(
    (index: number) => {
      if (index === -1) {
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

  const handleCreateCheckpoint = () => {
    if (!checkpointName.trim()) return;
    createCheckpointMutation.mutate(checkpointName, {
      onSuccess: () => {
        setCheckpointName("");
        toast.success("checkpoint created");
      },
    });
  };

  const handleRestore = (cpId: string) => {
    restoreCheckpointMutation.mutate(cpId, {
      onSuccess: () => {
        setPreviewId(null);
        toast.success("checkpoint restored");
      },
    });
  };

  const handleShare = async () => {
    try {
      const result = await chains.share(chainId);
      setShareUrl(result.share_url);
    } catch {
      toast.error("failed to create share link");
    }
  };

  const copyShareUrl = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopiedShare(true);
      setTimeout(() => setCopiedShare(false), 2000);
    }
  };

  const lastEntry = entries.length > 0 ? entries[entries.length - 1] : undefined;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        <Header
          title={chain?.name ?? "chain"}
          subtitle={chainLoading ? undefined : `${entries.length} entries`}
          actions={
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowCheckpoints(!showCheckpoints)}
                className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                <Save size={14} />
                checkpoints
              </button>
              <button
                onClick={handleShare}
                className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                <Share2 size={14} />
                share
              </button>
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
          {/* Share URL banner */}
          <AnimatePresence>
            {shareUrl && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-3 rounded-xl border border-pruv-500/30 bg-pruv-500/5 p-4"
              >
                <Share2 size={16} className="text-pruv-400 flex-shrink-0" />
                <code className="flex-1 text-xs font-mono text-pruv-400 truncate">
                  {shareUrl}
                </code>
                <button
                  onClick={copyShareUrl}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                >
                  {copiedShare ? (
                    <Check size={14} className="text-green-400" />
                  ) : (
                    <Copy size={14} />
                  )}
                </button>
                <button
                  onClick={() => setShareUrl(null)}
                  className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                >
                  dismiss
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Checkpoint panel */}
          <AnimatePresence>
            {showCheckpoints && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 space-y-4">
                  <h3 className="text-sm font-medium text-[var(--text-primary)]">
                    checkpoints
                  </h3>

                  {/* Create checkpoint */}
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={checkpointName}
                      onChange={(e) => setCheckpointName(e.target.value)}
                      placeholder="checkpoint name..."
                      className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none"
                    />
                    <button
                      onClick={handleCreateCheckpoint}
                      disabled={!checkpointName.trim() || createCheckpointMutation.isPending}
                      className="flex items-center gap-2 rounded-lg bg-pruv-600 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-500 transition-colors disabled:opacity-50"
                    >
                      {createCheckpointMutation.isPending ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Save size={14} />
                      )}
                      save
                    </button>
                  </div>

                  {/* Checkpoint list */}
                  {checkpointList.length === 0 ? (
                    <p className="text-xs text-[var(--text-tertiary)]">
                      no checkpoints yet — save one to enable restore
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {checkpointList.map((cp) => (
                        <div
                          key={cp.id}
                          className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3"
                        >
                          <div>
                            <span className="text-sm font-medium text-[var(--text-primary)]">
                              {cp.name}
                            </span>
                            <span className="ml-2 text-xs text-[var(--text-tertiary)]">
                              entry #{cp.entry_index}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() =>
                                setPreviewId(previewId === cp.id ? null : cp.id)
                              }
                              className="text-xs text-pruv-400 hover:text-pruv-300 transition-colors"
                            >
                              preview
                            </button>
                            <button
                              onClick={() => handleRestore(cp.id)}
                              disabled={restoreCheckpointMutation.isPending}
                              className="flex items-center gap-1 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                            >
                              {restoreCheckpointMutation.isPending ? (
                                <Loader2 size={12} className="animate-spin" />
                              ) : (
                                <RotateCcw size={12} />
                              )}
                              restore
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Preview panel */}
                  <AnimatePresence>
                    {previewId && previewData && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3"
                      >
                        <p className="text-xs text-yellow-400">
                          restoring to &quot;{previewData.checkpoint_name}&quot;
                          will roll back{" "}
                          <strong>
                            {previewData.entries_to_rollback} entries
                          </strong>{" "}
                          (entry #{previewData.target_entry_index} → #{previewData.current_entry_index})
                        </p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

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
