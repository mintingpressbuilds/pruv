"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Key,
  Plus,
  Copy,
  Check,
  Trash2,
  AlertTriangle,
  Eye,
  EyeOff,
  Loader2,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { toast } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { apiKeys } from "@/lib/api";
import type { ApiKey, ApiKeyScope, ApiKeyCreateResponse } from "@/lib/types";

const allScopes: { value: ApiKeyScope; label: string }[] = [
  { value: "chains:read", label: "chains:read" },
  { value: "chains:write", label: "chains:write" },
  { value: "entries:read", label: "entries:read" },
  { value: "entries:write", label: "entries:write" },
  { value: "receipts:read", label: "receipts:read" },
  { value: "receipts:create", label: "receipts:create" },
  { value: "scan:trigger", label: "scan:trigger" },
];

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyEnv, setNewKeyEnv] = useState<"live" | "test">("live");
  const [newKeyScopes, setNewKeyScopes] = useState<ApiKeyScope[]>([
    "chains:read",
    "entries:read",
    "receipts:read",
  ]);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreateResponse | null>(
    null
  );
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [revokeConfirm, setRevokeConfirm] = useState<string | null>(null);

  const { data: keys = [], isLoading } = useQuery<ApiKey[]>({
    queryKey: ["api-keys"],
    queryFn: () => apiKeys.list(),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiKeys.create({
        name: newKeyName,
        environment: newKeyEnv,
        scopes: newKeyScopes,
      }),
    onSuccess: (data) => {
      setCreatedKey(data);
      setShowCreate(false);
      setNewKeyName("");
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("api key created");
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => apiKeys.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setRevokeConfirm(null);
      toast.success("api key revoked");
    },
  });

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const toggleScope = (scope: ApiKeyScope) => {
    setNewKeyScopes((prev) =>
      prev.includes(scope)
        ? prev.filter((s) => s !== scope)
        : [...prev, scope]
    );
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-64">
        <Header
          title="api keys"
          actions={
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="flex items-center gap-2 rounded-lg bg-pruv-600 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-500 transition-colors"
            >
              <Plus size={14} />
              create key
            </button>
          }
        />

        <main className="p-6 max-w-3xl space-y-6">
          {/* Newly created key warning */}
          <AnimatePresence>
            {createdKey && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-5"
              >
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle size={16} className="text-yellow-400" />
                  <p className="text-sm font-medium text-yellow-400">
                    copy your api key now — it will not be shown again
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded-lg bg-[var(--surface)] px-4 py-3 font-mono text-sm text-[var(--text-primary)] border border-[var(--border)] break-all">
                    {createdKey.key}
                  </code>
                  <button
                    onClick={() => copyToClipboard(createdKey.key, "newkey")}
                    className="flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    {copiedField === "newkey" ? (
                      <Check size={16} className="text-green-400" />
                    ) : (
                      <Copy size={16} />
                    )}
                  </button>
                </div>
                <button
                  onClick={() => setCreatedKey(null)}
                  className="mt-3 text-xs text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                >
                  dismiss
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Create key form */}
          <AnimatePresence>
            {showCreate && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 space-y-4">
                  <h3 className="text-sm font-medium text-[var(--text-primary)]">
                    create new api key
                  </h3>

                  <div>
                    <label className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
                      name
                    </label>
                    <input
                      type="text"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      placeholder="e.g., production backend"
                      className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
                      environment
                    </label>
                    <div className="mt-1 flex items-center gap-3">
                      <button
                        onClick={() => setNewKeyEnv("live")}
                        className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-medium transition-colors ${
                          newKeyEnv === "live"
                            ? "border-pruv-500/50 bg-pruv-500/10 text-pruv-400"
                            : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)]"
                        }`}
                      >
                        <span className="font-mono">pv_live_</span>
                        production
                      </button>
                      <button
                        onClick={() => setNewKeyEnv("test")}
                        className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-medium transition-colors ${
                          newKeyEnv === "test"
                            ? "border-yellow-500/50 bg-yellow-500/10 text-yellow-400"
                            : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)]"
                        }`}
                      >
                        <span className="font-mono">pv_test_</span>
                        testing
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
                      scopes
                    </label>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {allScopes.map((scope) => (
                        <button
                          key={scope.value}
                          onClick={() => toggleScope(scope.value)}
                          className={`rounded-full border px-2.5 py-1 text-[10px] font-mono transition-colors ${
                            newKeyScopes.includes(scope.value)
                              ? "border-pruv-500/50 bg-pruv-500/10 text-pruv-400"
                              : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-tertiary)]"
                          }`}
                        >
                          {scope.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 pt-2">
                    <button
                      onClick={() => createMutation.mutate()}
                      disabled={
                        !newKeyName || newKeyScopes.length === 0 || createMutation.isPending
                      }
                      className="flex items-center gap-2 rounded-lg bg-pruv-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-pruv-500 transition-colors disabled:opacity-50"
                    >
                      {createMutation.isPending ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Key size={14} />
                      )}
                      create key
                    </button>
                    <button
                      onClick={() => setShowCreate(false)}
                      className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                    >
                      cancel
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Key list */}
          <div>
            <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
              your api keys
            </h3>

            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4 animate-pulse"
                  >
                    <div className="h-4 w-40 rounded bg-[var(--surface-tertiary)]" />
                    <div className="mt-2 h-3 w-24 rounded bg-[var(--surface-tertiary)]" />
                  </div>
                ))}
              </div>
            ) : keys.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[var(--border)] p-10 text-center">
                <Key
                  size={24}
                  className="mx-auto text-[var(--text-tertiary)] mb-2"
                />
                <p className="text-sm text-[var(--text-secondary)]">
                  no api keys yet
                </p>
                <p className="mt-1 text-xs text-[var(--text-tertiary)]">
                  create a key to start using the pruv api
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {keys.map((key, i) => (
                  <motion.div
                    key={key.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[var(--text-primary)]">
                          {key.name}
                        </span>
                        <span
                          className={`rounded-full border px-2 py-0.5 text-[10px] font-mono ${
                            key.environment === "live"
                              ? "border-pruv-500/20 bg-pruv-500/10 text-pruv-400"
                              : "border-yellow-500/20 bg-yellow-500/10 text-yellow-400"
                          }`}
                        >
                          {key.prefix}...
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
                        <span>
                          created{" "}
                          {formatDistanceToNow(new Date(key.created_at), {
                            addSuffix: true,
                          })}
                        </span>
                        {key.last_used_at && (
                          <span>
                            last used{" "}
                            {formatDistanceToNow(new Date(key.last_used_at), {
                              addSuffix: true,
                            })}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          {key.scopes.length} scopes
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {revokeConfirm === key.id ? (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-red-400">revoke?</span>
                          <button
                            onClick={() => revokeMutation.mutate(key.id)}
                            disabled={revokeMutation.isPending}
                            className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/20 transition-colors"
                          >
                            confirm
                          </button>
                          <button
                            onClick={() => setRevokeConfirm(null)}
                            className="text-xs text-[var(--text-tertiary)]"
                          >
                            cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setRevokeConfirm(key.id)}
                          className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:text-red-400 hover:border-red-500/30 transition-colors"
                        >
                          <Trash2 size={12} />
                          revoke
                        </button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* Environment variable hint */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
            <h4 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
              usage
            </h4>
            <div className="space-y-2">
              <div className="rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                <code className="text-xs text-pruv-400 font-mono">
                  export PRUV_API_KEY=pv_live_...
                </code>
              </div>
              <p className="text-xs text-[var(--text-tertiary)]">
                set your api key as an environment variable to authenticate
                with the pruv api at api.pruv.dev
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
