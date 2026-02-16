"use client";

import { useState, useCallback, useMemo } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Save,
  RotateCcw,
  Loader2,
  Share2,
  Copy,
  Check,
  Download,
  AlertTriangle,
  Bot,
  DollarSign,
} from "lucide-react";
import { toast } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { ChainTimeline } from "@/components/chain-timeline";
import { TimeTravel } from "@/components/time-travel";
import { ReplayControls } from "@/components/replay-controls";
import { VerificationBadge } from "@/components/verification-badge";
import { QuickUndo } from "@/components/quick-undo";
import { useChain, useChainVerification, useChainAlerts, usePaymentVerification } from "@/hooks/use-chains";
import { useEntries, useUndoEntry } from "@/hooks/use-entries";
import {
  useCheckpoints,
  useCreateCheckpoint,
  useCheckpointPreview,
  useRestoreCheckpoint,
} from "@/hooks/use-checkpoints";
import { chains } from "@/lib/api";
import { isPaymentEntry } from "@/components/entry-node";
import type { Entry, AlertSeverity } from "@/lib/types";

const severityConfig: Record<
  AlertSeverity,
  { label: string; color: string; border: string }
> = {
  info: {
    label: "info",
    color: "text-blue-400",
    border: "border-blue-500/20 bg-blue-500/5",
  },
  warning: {
    label: "warning",
    color: "text-yellow-400",
    border: "border-yellow-500/20 bg-yellow-500/5",
  },
  critical: {
    label: "critical",
    color: "text-red-400",
    border: "border-red-500/20 bg-red-500/5",
  },
};

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
  const { data: alertsData } = useChainAlerts(chainId);
  const {
    data: paymentVerification,
    isLoading: isVerifyingPayments,
    refetch: runPaymentVerification,
  } = usePaymentVerification(chainId, { enabled: false });

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

  // Filter state
  const [actionFilter, setActionFilter] = useState("");

  const entries: Entry[] = entriesData?.data ?? [];
  const [timeTravelIndex, setTimeTravelIndex] = useState<number>(entries.length - 1);

  // Derive unique action types for the filter dropdown
  const actionTypes = useMemo(() => {
    const types = new Set(entries.map((e) => e.action));
    return Array.from(types).sort();
  }, [entries]);

  // Apply filters
  const filteredEntries = useMemo(() => {
    let result = entries;
    if (actionFilter) {
      result = result.filter((e) => e.action === actionFilter);
    }
    return result;
  }, [entries, actionFilter]);

  const displayEntries = useMemo(() => {
    if (!actionFilter && timeTravelIndex >= 0 && timeTravelIndex < entries.length) {
      return entries.slice(0, timeTravelIndex + 1);
    }
    return filteredEntries;
  }, [entries, filteredEntries, actionFilter, timeTravelIndex]);

  // Alert summary
  const alerts = alertsData?.alerts ?? [];
  const warningCount = alerts.filter((a) => a.severity === "warning").length;
  const criticalCount = alerts.filter((a) => a.severity === "critical").length;

  // Agent metadata
  const agentName = chain?.metadata?.agent as string | undefined;
  const framework = chain?.metadata?.framework as string | undefined;

  // Payment summary
  const paymentEntryCount = useMemo(
    () => entries.filter(isPaymentEntry).length,
    [entries]
  );
  const hasPayments = paymentEntryCount > 0;

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

  const handleVerifyPayments = () => {
    runPaymentVerification();
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

  const handleExport = async () => {
    try {
      const html = await chains.exportHtml(chainId);
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${chain?.name ?? chainId}-export.html`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("chain exported");
    } catch {
      toast.error("failed to export chain");
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
                onClick={handleExport}
                className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                <Download size={14} />
                export
              </button>
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
              {hasPayments && (
                <button
                  onClick={handleVerifyPayments}
                  disabled={isVerifyingPayments}
                  className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm font-medium text-emerald-400 hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
                >
                  {isVerifyingPayments ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <DollarSign size={14} />
                  )}
                  verify payments
                </button>
              )}
            </div>
          }
        />

        <main className="p-6 space-y-6">
          {/* Alert summary banner */}
          {alerts.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4"
            >
              <AlertTriangle
                size={16}
                className={criticalCount > 0 ? "text-red-400" : "text-yellow-400"}
              />
              <div className="flex items-center gap-3 text-xs">
                {criticalCount > 0 && (
                  <span className="text-red-400 font-medium">
                    {criticalCount} critical
                  </span>
                )}
                {warningCount > 0 && (
                  <span className="text-yellow-400 font-medium">
                    {warningCount} warning{warningCount !== 1 ? "s" : ""}
                  </span>
                )}
                {alerts.length - criticalCount - warningCount > 0 && (
                  <span className="text-blue-400 font-medium">
                    {alerts.length - criticalCount - warningCount} info
                  </span>
                )}
              </div>
              <div className="flex-1" />
              <div className="flex flex-wrap gap-2">
                {alerts.slice(0, 3).map((alert, i) => {
                  const config = severityConfig[alert.severity];
                  return (
                    <span
                      key={i}
                      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] ${config.border} ${config.color}`}
                    >
                      {alert.message}
                    </span>
                  );
                })}
                {alerts.length > 3 && (
                  <span className="text-[10px] text-[var(--text-tertiary)]">
                    +{alerts.length - 3} more
                  </span>
                )}
              </div>
            </motion.div>
          )}

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
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                      {chain.name}
                    </h2>
                    {agentName && (
                      <span className="inline-flex items-center gap-1 rounded-full border border-pruv-500/20 bg-pruv-500/10 px-2 py-0.5 text-[10px] font-medium text-pruv-400">
                        <Bot size={10} />
                        {agentName}
                      </span>
                    )}
                    {framework && (
                      <span className="inline-flex items-center rounded-full border border-blue-500/20 bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-400">
                        {framework}
                      </span>
                    )}
                  </div>
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

              {/* Payment summary */}
              {hasPayments && (
                <div className="mt-4 flex items-center gap-6 border-t border-[var(--border)] pt-3">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rotate-45 rounded-sm bg-emerald-500" />
                    <span className="text-xs text-[var(--text-secondary)]">
                      <span className="font-medium text-[var(--text-primary)]">{paymentEntryCount}</span> payment{paymentEntryCount !== 1 ? "s" : ""}
                    </span>
                  </div>
                  {paymentVerification && (
                    <>
                      <span className="text-xs text-[var(--text-secondary)]">
                        <span className="font-medium text-[var(--text-primary)]">{paymentVerification.verified_count}</span> verified
                      </span>
                      <span className="text-xs font-mono text-[var(--text-secondary)]">
                        $<span className="font-medium text-[var(--text-primary)]">
                          {paymentVerification.total_volume.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span> volume
                      </span>
                      {paymentVerification.all_valid ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-green-400">
                          <Check size={10} />
                          all valid
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-red-400">
                          <AlertTriangle size={10} />
                          {paymentVerification.breaks.length} break{paymentVerification.breaks.length !== 1 ? "s" : ""}
                        </span>
                      )}
                    </>
                  )}
                  <span className="text-xs text-[var(--text-secondary)]">
                    <span className="font-medium text-[var(--text-primary)]">{entries.length - paymentEntryCount}</span> operation{entries.length - paymentEntryCount !== 1 ? "s" : ""}
                  </span>
                </div>
              )}
            </motion.div>
          )}

          {/* Payment verification result banner */}
          <AnimatePresence>
            {paymentVerification && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`flex items-center gap-4 rounded-xl border p-4 ${
                  paymentVerification.all_valid
                    ? "border-green-500/30 bg-green-500/5"
                    : "border-red-500/30 bg-red-500/5"
                }`}
              >
                <DollarSign
                  size={16}
                  className={paymentVerification.all_valid ? "text-green-400" : "text-red-400"}
                />
                <span className={`text-sm ${paymentVerification.all_valid ? "text-green-400" : "text-red-400"}`}>
                  {paymentVerification.message}
                </span>
                {paymentVerification.final_balances && Object.keys(paymentVerification.final_balances).length > 0 && (
                  <div className="ml-auto flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
                    {Object.entries(paymentVerification.final_balances).slice(0, 4).map(([account, balance]) => (
                      <span key={account} className="font-mono">
                        {account}: ${balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    ))}
                    {Object.keys(paymentVerification.final_balances).length > 4 && (
                      <span>+{Object.keys(paymentVerification.final_balances).length - 4} more</span>
                    )}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Time travel + replay controls */}
          {entries.length > 1 && !actionFilter && (
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
            actionFilter={actionFilter}
            onActionFilterChange={setActionFilter}
            actionTypes={actionTypes}
          />
        </main>
      </div>
    </div>
  );
}
