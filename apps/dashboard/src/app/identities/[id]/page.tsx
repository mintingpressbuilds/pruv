"use client";

import { use } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Fingerprint,
  CheckCircle2,
  XCircle,
  Shield,
  Clock,
  FileDown,
  Copy,
  Check,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { toast } from "sonner";
import { useState } from "react";
import {
  useIdentity,
  useIdentityVerification,
  useIdentityHistory,
} from "@/hooks/use-identities";
import { identities } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";

const agentTypeLabels: Record<string, string> = {
  langchain: "LangChain",
  crewai: "CrewAI",
  openai_agents: "OpenAI Agents",
  custom: "Custom",
};

export default function IdentityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: identity, isLoading } = useIdentity(id);
  const { data: verification, refetch: reverify } =
    useIdentityVerification(id);
  const { data: historyData } = useIdentityHistory(id, { limit: 50 });
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

  const actions = historyData?.actions ?? [];

  let content: React.ReactNode;

  if (isLoading) {
    content = (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="h-8 w-48 rounded bg-[var(--surface-secondary)] animate-pulse mb-6" />
        <div className="h-64 rounded-lg bg-[var(--surface-secondary)] animate-pulse" />
      </div>
    );
  } else if (!identity) {
    content = (
      <div className="p-6 max-w-5xl mx-auto text-center py-16">
        <XCircle
          size={48}
          className="mx-auto mb-4 text-[var(--text-tertiary)]"
        />
        <p className="text-[var(--text-secondary)]">Identity not found.</p>
        <Link
          href="/identities"
          className="mt-4 inline-block text-sm text-pruv-500 hover:text-pruv-400"
        >
          Back to identities
        </Link>
      </div>
    );
  } else {
    content = (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <Link
        href="/identities"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] mb-4 transition-colors"
      >
        <ArrowLeft size={14} />
        Identities
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pruv-500/10">
            <Fingerprint size={24} className="text-pruv-500" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[var(--text-primary)]">
              {identity.name}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                {agentTypeLabels[identity.agent_type] ?? identity.agent_type}
              </span>
              <span className="text-xs text-[var(--text-tertiary)] font-mono">
                {identity.id}
              </span>
              <button
                onClick={() => copyToClipboard(identity.id, "Address")}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
              >
                {copied === "Address" ? (
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
            href={identities.getReceiptUrl(id)}
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
            Actions
          </div>
          <div className="text-2xl font-semibold text-[var(--text-primary)]">
            {identity.action_count}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-xs text-[var(--text-tertiary)] mb-1">
            Status
          </div>
          <div className="text-sm font-medium text-pruv-500 mt-1">
            {verification?.valid ? "Verified" : "Pending"}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-xs text-[var(--text-tertiary)] mb-1">
            Registered
          </div>
          <div className="text-sm text-[var(--text-primary)] mt-1">
            {format(new Date(identity.registered_at), "MMM d, yyyy")}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="text-xs text-[var(--text-tertiary)] mb-1">
            Last Active
          </div>
          <div className="text-sm text-[var(--text-primary)] mt-1">
            {identity.last_action_at
              ? formatDistanceToNow(new Date(identity.last_action_at), {
                  addSuffix: true,
                })
              : "Never"}
          </div>
        </div>
      </div>

      {/* Public Key */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4 mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-[var(--text-tertiary)]">
            Public Key
          </span>
          <button
            onClick={() =>
              copyToClipboard(identity.public_key, "Public key")
            }
            className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] flex items-center gap-1"
          >
            {copied === "Public key" ? (
              <Check size={12} />
            ) : (
              <Copy size={12} />
            )}
            Copy
          </button>
        </div>
        <div className="font-mono text-xs text-[var(--text-secondary)] break-all">
          {identity.public_key}
        </div>
      </div>

      {/* Chain Link */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-[var(--text-tertiary)]">
              Underlying Chain
            </span>
            <div className="font-mono text-sm text-[var(--text-primary)] mt-1">
              {identity.chain_id}
            </div>
          </div>
          <Link
            href={`/chains/${identity.chain_id}`}
            className="text-xs text-pruv-500 hover:text-pruv-400"
          >
            View chain
          </Link>
        </div>
      </div>

      {/* Action History */}
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
          Action History
        </h2>
        {actions.length === 0 ? (
          <div className="text-center py-8 text-sm text-[var(--text-tertiary)]">
            No actions recorded yet.
          </div>
        ) : (
          <div className="space-y-0">
            {(actions as Array<Record<string, unknown>>).map(
              (action, idx) => {
                const timestamp = action.timestamp as number | undefined;
                const operation =
                  (action.operation as string) ?? "unknown";
                const index = (action.index as number) ?? idx;

                return (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -4 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.02 }}
                    className="flex items-start gap-3 border-l-2 border-[var(--border)] pl-4 py-2 hover:border-pruv-500 transition-colors"
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
                      {timestamp && (
                        <div className="flex items-center gap-1 mt-0.5 text-xs text-[var(--text-tertiary)]">
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
              }
            )}
          </div>
        )}
      </div>
    </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        {content}
      </div>
    </div>
  );
}
