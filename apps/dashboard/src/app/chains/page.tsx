"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Search,
  Link2,
  AlertTriangle,
  ShieldCheck,
  Plus,
  Bot,
  X,
  Copy,
  Check,
  Zap,
  Wallet,
  Settings2,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { useChains, useCreateChain } from "@/hooks/use-chains";
import type { Chain, ChainStatus, ChainType, ChainFilters } from "@/lib/types";

const statusConfig: Record<
  ChainStatus,
  { label: string; color: string; dotColor: string }
> = {
  valid: {
    label: "valid",
    color: "text-green-400 bg-green-500/10 border-green-500/20",
    dotColor: "bg-green-500",
  },
  broken: {
    label: "broken",
    color: "text-red-400 bg-red-500/10 border-red-500/20",
    dotColor: "bg-red-500",
  },
  pending: {
    label: "pending",
    color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
    dotColor: "bg-yellow-500",
  },
  archived: {
    label: "archived",
    color: "text-[var(--text-tertiary)] bg-[var(--surface-tertiary)] border-[var(--border)]",
    dotColor: "bg-[var(--text-tertiary)]",
  },
};

const chainTypeConfig: Record<
  ChainType,
  { label: string; icon: typeof Zap; color: string; description: string }
> = {
  operations: {
    label: "operations",
    icon: Zap,
    color: "text-purple-400 bg-purple-500/10 border-purple-500/20",
    description: "agent actions, deployments, system events",
  },
  payments: {
    label: "payments",
    icon: Wallet,
    color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description: "transfers, deposits, balance tracking",
  },
  custom: {
    label: "custom",
    icon: Settings2,
    color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    description: "you decide what goes in",
  },
};

function getCodeSnippet(chainType: ChainType, chainName: string, chainId: string): string {
  if (chainType === "operations") {
    return `from pruv import Agent

agent = Agent("${chainName}", api_key="pv_live_xxxxx")
agent.action("deployed", {"version": "2.1.0"})`;
  }
  if (chainType === "payments") {
    return `from pruv import PaymentChain

ledger = PaymentChain("${chainName}", api_key="pv_live_xxxxx")
ledger.deposit("merchant", 10000.00, source="bank")
ledger.transfer("merchant", "customer", 250.00, source="stripe")`;
  }
  return `from pruv import Agent

agent = Agent("${chainName}", api_key="pv_live_xxxxx")
agent.action("my_event", {"key": "value"})`;
}

export default function ChainsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<ChainFilters>({
    sort_by: "updated_at",
    sort_order: "desc",
    page: 1,
    per_page: 20,
  });
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ChainStatus | "">("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newChainName, setNewChainName] = useState("");
  const [newChainDesc, setNewChainDesc] = useState("");
  const [newChainType, setNewChainType] = useState<ChainType>("operations");
  const [createdChain, setCreatedChain] = useState<Chain | null>(null);
  const [copied, setCopied] = useState(false);

  const { data, isLoading } = useChains({
    ...filters,
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const createChain = useCreateChain();

  const handleCreateChain = async () => {
    const name = newChainName.trim();
    if (!name) return;

    try {
      const chain = await createChain.mutateAsync({
        name,
        description: newChainDesc.trim() || undefined,
        chain_type: newChainType,
      });
      setCreatedChain(chain);
      toast.success("chain created");
    } catch {
      toast.error("failed to create chain");
    }
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
    setNewChainName("");
    setNewChainDesc("");
    setNewChainType("operations");
    if (createdChain) {
      router.push(`/chains/${createdChain.id}`);
      setCreatedChain(null);
    }
  };

  const handleCopySnippet = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const chains = data?.data ?? [];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        <Header
          title="chains"
          actions={
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 rounded-lg bg-pruv-600 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-500 transition-colors"
            >
              <Plus size={14} />
              new chain
            </button>
          }
        />

        <main className="p-6 space-y-4">
          {/* Filters bar */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]"
              />
              <input
                type="text"
                placeholder="search chains..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none focus:ring-1 focus:ring-pruv-500/20 transition-all"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ChainStatus | "")}
              className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-secondary)] focus:border-pruv-500/50 focus:outline-none"
            >
              <option value="">all statuses</option>
              <option value="valid">valid</option>
              <option value="broken">broken</option>
              <option value="pending">pending</option>
              <option value="archived">archived</option>
            </select>

            <select
              value={`${filters.sort_by}:${filters.sort_order}`}
              onChange={(e) => {
                const [sort_by, sort_order] = e.target.value.split(":") as [
                  ChainFilters["sort_by"],
                  ChainFilters["sort_order"],
                ];
                setFilters((f) => ({ ...f, sort_by, sort_order }));
              }}
              className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-secondary)] focus:border-pruv-500/50 focus:outline-none"
            >
              <option value="updated_at:desc">recently updated</option>
              <option value="created_at:desc">newest first</option>
              <option value="name:asc">name (a-z)</option>
              <option value="entry_count:desc">most entries</option>
            </select>
          </div>

          {/* Chain list */}
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 animate-pulse"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="h-4 w-48 rounded bg-[var(--surface-tertiary)]" />
                      <div className="mt-2 h-3 w-32 rounded bg-[var(--surface-tertiary)]" />
                    </div>
                    <div className="h-6 w-16 rounded-full bg-[var(--surface-tertiary)]" />
                  </div>
                </div>
              ))}
            </div>
          ) : chains.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--surface-secondary)] border border-[var(--border)] mb-4">
                <Link2 size={24} className="text-[var(--text-tertiary)]" />
              </div>
              <p className="text-sm text-[var(--text-secondary)]">
                {search ? "no chains match your search" : "no chains yet"}
              </p>
              <p className="mt-1 text-xs text-[var(--text-tertiary)]">
                create your first chain with{" "}
                <code className="rounded bg-[var(--surface-tertiary)] px-1.5 py-0.5 text-pruv-400">
                  pip install pruv
                </code>
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {chains.map((chain, i) => {
                const status = statusConfig[chain.status];
                const agentName = chain.metadata?.agent as string | undefined;
                const framework = chain.metadata?.framework as string | undefined;
                const typeConf = chainTypeConfig[chain.chain_type] ?? chainTypeConfig.custom;
                const TypeIcon = typeConf.icon;
                return (
                  <motion.div
                    key={chain.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                  >
                    <Link
                      href={`/chains/${chain.id}`}
                      className="group flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 hover:border-pruv-500/30 transition-all duration-200"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                          <h3 className="text-sm font-medium text-[var(--text-primary)] group-hover:text-pruv-400 transition-colors truncate">
                            {chain.name}
                          </h3>
                          <span
                            className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${status.color}`}
                          >
                            <span className={`h-1.5 w-1.5 rounded-full ${status.dotColor}`} />
                            {status.label}
                          </span>
                          <span
                            className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${typeConf.color}`}
                          >
                            <TypeIcon size={10} />
                            {typeConf.label}
                          </span>
                          {framework && (
                            <span className="inline-flex items-center gap-1 rounded-full border border-blue-500/20 bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-400">
                              {framework}
                            </span>
                          )}
                        </div>
                        {chain.description && (
                          <p className="mt-1 text-xs text-[var(--text-tertiary)] truncate max-w-md">
                            {chain.description}
                          </p>
                        )}
                        <div className="mt-2 flex items-center gap-4 text-xs text-[var(--text-tertiary)]">
                          {agentName && (
                            <span className="flex items-center gap-1">
                              <Bot size={12} />
                              {agentName}
                            </span>
                          )}
                          <span>{chain.entry_count} entries</span>
                          {chain.tags.length > 0 && (
                            <div className="flex items-center gap-1">
                              {chain.tags.slice(0, 3).map((tag) => (
                                <span
                                  key={tag}
                                  className="rounded bg-[var(--surface-tertiary)] px-1.5 py-0.5 text-[10px]"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                          <span>
                            updated{" "}
                            {formatDistanceToNow(new Date(chain.updated_at), {
                              addSuffix: true,
                            })}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 ml-4">
                        {chain.status === "valid" && (
                          <ShieldCheck size={16} className="text-green-400" />
                        )}
                        {chain.status === "broken" && (
                          <AlertTriangle size={16} className="text-red-400" />
                        )}
                      </div>
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          )}

          {/* Pagination / summary */}
          {data && data.total > 0 && (
            <div className="flex items-center justify-between pt-4 text-xs text-[var(--text-tertiary)]">
              <span>
                showing {chains.length} of {data.total} chains
              </span>
              {data.has_more && (
                <button
                  onClick={() =>
                    setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))
                  }
                  className="text-pruv-400 hover:text-pruv-300"
                >
                  load more
                </button>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Create chain modal */}
      <AnimatePresence>
        {showCreateModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleCloseModal}
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-6 shadow-2xl max-h-[90vh] overflow-y-auto"
            >
              {/* Success screen */}
              {createdChain ? (
                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/10">
                        <Check size={16} className="text-green-400" />
                      </div>
                      <h2 className="text-base font-semibold text-[var(--text-primary)]">
                        chain created
                      </h2>
                    </div>
                    <button
                      onClick={handleCloseModal}
                      className="rounded-md p-1 text-[var(--text-tertiary)] hover:bg-[var(--surface-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <X size={16} />
                    </button>
                  </div>

                  <div className="rounded-lg bg-[var(--surface)] border border-[var(--border)] p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[var(--text-tertiary)]">chain id</span>
                      <code className="text-sm font-mono text-pruv-400">{createdChain.id}</code>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[var(--text-tertiary)]">type</span>
                      <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${chainTypeConfig[createdChain.chain_type]?.color ?? chainTypeConfig.custom.color}`}>
                        {createdChain.chain_type}
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-[var(--text-secondary)]">
                        add entries
                      </span>
                      <button
                        onClick={() =>
                          handleCopySnippet(
                            getCodeSnippet(createdChain.chain_type, createdChain.name, createdChain.id)
                          )
                        }
                        className="flex items-center gap-1 text-[10px] text-[var(--text-tertiary)] hover:text-pruv-400 transition-colors"
                      >
                        {copied ? <Check size={10} /> : <Copy size={10} />}
                        {copied ? "copied" : "copy"}
                      </button>
                    </div>
                    <pre className="rounded-lg bg-[var(--surface)] border border-[var(--border)] p-4 text-xs font-mono text-[var(--text-primary)] overflow-x-auto whitespace-pre">
                      {getCodeSnippet(createdChain.chain_type, createdChain.name, createdChain.id)}
                    </pre>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2">
                    <button
                      onClick={handleCloseModal}
                      className="rounded-lg bg-pruv-600 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-500 transition-colors"
                    >
                      go to chain
                    </button>
                  </div>
                </div>
              ) : (
                /* Create form */
                <>
                  <div className="flex items-center justify-between mb-5">
                    <h2 className="text-base font-semibold text-[var(--text-primary)]">
                      new chain
                    </h2>
                    <button
                      onClick={handleCloseModal}
                      className="rounded-md p-1 text-[var(--text-tertiary)] hover:bg-[var(--surface-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <X size={16} />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                        name
                      </label>
                      <input
                        type="text"
                        value={newChainName}
                        onChange={(e) => setNewChainName(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleCreateChain()}
                        placeholder="my-agent-chain"
                        autoFocus
                        className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-primary)] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none focus:ring-1 focus:ring-pruv-500/20 transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                        description{" "}
                        <span className="text-[var(--text-tertiary)]">
                          (optional)
                        </span>
                      </label>
                      <input
                        type="text"
                        value={newChainDesc}
                        onChange={(e) => setNewChainDesc(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleCreateChain()}
                        placeholder="what this chain tracks"
                        className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-primary)] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none focus:ring-1 focus:ring-pruv-500/20 transition-all"
                      />
                    </div>

                    {/* Chain type selector */}
                    <div>
                      <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
                        type
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {(Object.keys(chainTypeConfig) as ChainType[]).map((type) => {
                          const conf = chainTypeConfig[type];
                          const Icon = conf.icon;
                          const isSelected = newChainType === type;
                          return (
                            <button
                              key={type}
                              type="button"
                              onClick={() => setNewChainType(type)}
                              className={`flex flex-col items-center gap-1.5 rounded-lg border p-3 text-center transition-all ${
                                isSelected
                                  ? "border-pruv-500/50 bg-pruv-500/5 ring-1 ring-pruv-500/20"
                                  : "border-[var(--border)] bg-[var(--surface)] hover:border-[var(--border-secondary)]"
                              }`}
                            >
                              <Icon
                                size={16}
                                className={isSelected ? "text-pruv-400" : "text-[var(--text-tertiary)]"}
                              />
                              <span
                                className={`text-xs font-medium ${
                                  isSelected ? "text-pruv-400" : "text-[var(--text-secondary)]"
                                }`}
                              >
                                {conf.label}
                              </span>
                              <span className="text-[10px] text-[var(--text-tertiary)] leading-tight">
                                {conf.description}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-2">
                      <button
                        onClick={handleCloseModal}
                        className="rounded-lg border border-[var(--border)] bg-transparent px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] transition-colors"
                      >
                        cancel
                      </button>
                      <button
                        onClick={handleCreateChain}
                        disabled={
                          !newChainName.trim() || createChain.isPending
                        }
                        className="rounded-lg bg-pruv-600 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {createChain.isPending ? "creating..." : "create chain"}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
