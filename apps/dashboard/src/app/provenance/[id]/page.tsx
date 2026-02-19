"use client";

import { use, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  FileSearch,
  CheckCircle2,
  XCircle,
  Shield,
  Clock,
  FileDown,
  Copy,
  Check,
  ArrowRight,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { toast } from "sonner";
import {
  useArtifact,
  useProvenanceVerification,
  useProvenanceHistory,
} from "@/hooks/use-provenance";
import { provenanceApi } from "@/lib/api";

export default function ProvenanceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: artifact, isLoading } = useArtifact(id);
  const { data: verification, refetch: reverify } =
    useProvenanceVerification(id);
  const { data: historyData } = useProvenanceHistory(id, { limit: 50 });
  const [copied, setCopied] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    toast.success(`${label} copied`);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleVerify = async () => {
    setVerifying(true);
    await reverify();
    setVerifying(false);
    toast.success("Verification complete");
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="h-8 w-48 rounded bg-[var(--surface-secondary)] animate-pulse mb-6" />
        <div className="h-64 rounded-lg bg-[var(--surface-secondary)] animate-pulse" />
      </div>
    );
  }

  if (!artifact) {
    return (
      <div className="p-6 max-w-5xl mx-auto text-center py-16">
        <XCircle
          size={48}
          className="mx-auto mb-4 text-[var(--text-tertiary)]"
        />
        <p className="text-[var(--text-secondary)]">Artifact not found.</p>
        <Link
          href="/provenance"
          className="mt-4 inline-block text-sm text-pruv-500 hover:text-pruv-400"
        >
          Back to provenance
        </Link>
      </div>
    );
  }

  const entries = historyData?.entries ?? [];

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <Link
        href="/provenance"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] mb-4 transition-colors"
      >
        <ArrowLeft size={14} />
        Provenance
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pruv-500/10">
            <FileSearch size={24} className="text-pruv-500" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[var(--text-primary)]">
              {artifact.name}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                {artifact.content_type}
              </span>
              <span className="text-xs text-[var(--text-tertiary)] font-mono">
                {artifact.id}
              </span>
              <button
                onClick={() => copyToClipboard(artifact.id, "ID")}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
              >
                {copied === "ID" ? (
                  <Check size={12} />
                ) : (
                  <Copy size={12} />
                )}
              </button>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] disabled:opacity-50 transition-colors"
          >
            <Shield size={14} />
            {verifying ? "Verifying..." : "Verify"}
          </button>
          <a
            href={provenanceApi.getReceiptUrl(id)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] transition-colors"
          >
            <FileDown size={14} />
            Export Receipt
          </a>
        </div>
      </div>

      {/* Verification Status */}
      {verification && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-lg border p-4 mb-6 ${
            verification.valid
              ? "border-pruv-500/30 bg-pruv-500/5"
              : "border-red-500/30 bg-red-500/5"
          }`}
        >
          <div className="flex items-center gap-2">
            {verification.valid ? (
              <CheckCircle2 size={16} className="text-pruv-500" />
            ) : (
              <XCircle size={16} className="text-red-500" />
            )}
            <span
              className={`text-sm font-medium ${
                verification.valid ? "text-pruv-600" : "text-red-600"
              }`}
            >
              {verification.message}
            </span>
          </div>
        </motion.div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-xs text-[var(--text-tertiary)] mb-1">
            Creator
          </div>
          <div className="text-sm font-medium text-[var(--text-primary)] truncate">
            {artifact.creator}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-xs text-[var(--text-tertiary)] mb-1">
            Modifications
          </div>
          <div className="text-2xl font-semibold text-[var(--text-primary)]">
            {artifact.transition_count}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-xs text-[var(--text-tertiary)] mb-1">
            Registered
          </div>
          <div className="text-sm text-[var(--text-primary)] mt-1">
            {format(new Date(artifact.created_at), "MMM d, yyyy")}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-xs text-[var(--text-tertiary)] mb-1">
            Last Modified
          </div>
          <div className="text-sm text-[var(--text-primary)] mt-1">
            {artifact.last_modified_at
              ? formatDistanceToNow(new Date(artifact.last_modified_at), {
                  addSuffix: true,
                })
              : "Never"}
          </div>
        </div>
      </div>

      {/* Origin Hash */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4 mb-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-[var(--text-tertiary)]">
            Origin Hash
          </span>
          <button
            onClick={() =>
              copyToClipboard(artifact.content_hash, "Origin hash")
            }
            className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] flex items-center gap-1"
          >
            {copied === "Origin hash" ? (
              <Check size={12} />
            ) : (
              <Copy size={12} />
            )}
            Copy
          </button>
        </div>
        <div className="font-mono text-xs text-[var(--text-secondary)] break-all">
          {artifact.content_hash}
        </div>
      </div>

      {/* Current Hash */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4 mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-[var(--text-tertiary)]">
            Current Hash
          </span>
          <button
            onClick={() =>
              copyToClipboard(artifact.current_hash, "Current hash")
            }
            className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] flex items-center gap-1"
          >
            {copied === "Current hash" ? (
              <Check size={12} />
            ) : (
              <Copy size={12} />
            )}
            Copy
          </button>
        </div>
        <div className="font-mono text-xs text-[var(--text-secondary)] break-all">
          {artifact.current_hash}
        </div>
        {artifact.content_hash !== artifact.current_hash && (
          <div className="mt-2 text-xs text-amber-500">
            Content has been modified from origin
          </div>
        )}
      </div>

      {/* Chain Link */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-[var(--text-tertiary)]">
              Underlying Chain
            </span>
            <div className="font-mono text-sm text-[var(--text-primary)] mt-1">
              {artifact.chain_id}
            </div>
          </div>
          <Link
            href={`/chains/${artifact.chain_id}`}
            className="text-xs text-pruv-500 hover:text-pruv-400"
          >
            View chain
          </Link>
        </div>
      </div>

      {/* Modification History */}
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
          Modification History
        </h2>
        {entries.length === 0 ? (
          <div className="text-center py-8 text-sm text-[var(--text-tertiary)]">
            No modifications recorded yet.
          </div>
        ) : (
          <div className="space-y-0">
            {(entries as Array<Record<string, unknown>>).map((entry, idx) => {
              const timestamp = entry.timestamp as number | undefined;
              const operation = (entry.operation as string) ?? "unknown";
              const index = (entry.index as number) ?? idx;
              const xState = entry.x_state as Record<string, unknown> | undefined;
              const yState = entry.y_state as Record<string, unknown> | undefined;
              const previousHash = (xState?.content_hash as string) ?? null;
              const newHash = (yState?.content_hash as string) ?? null;

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  className="flex items-start gap-3 border-l-2 border-[var(--border)] pl-4 py-3 hover:border-pruv-500 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[var(--text-tertiary)] font-mono">
                        #{index}
                      </span>
                      <span className="text-sm font-medium text-[var(--text-primary)]">
                        {operation}
                      </span>
                    </div>
                    {previousHash && newHash && (
                      <div className="flex items-center gap-1.5 mt-1.5 text-xs font-mono text-[var(--text-tertiary)]">
                        <span className="truncate max-w-[120px]" title={previousHash}>
                          {previousHash.slice(0, 12)}...
                        </span>
                        <ArrowRight size={10} className="shrink-0" />
                        <span className="truncate max-w-[120px]" title={newHash}>
                          {newHash.slice(0, 12)}...
                        </span>
                      </div>
                    )}
                    {timestamp && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-[var(--text-tertiary)]">
                        <Clock size={10} />
                        {format(
                          new Date(timestamp * 1000),
                          "MMM d, yyyy HH:mm:ss"
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
