"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Fingerprint,
  Plus,
  CheckCircle2,
  XCircle,
  Search,
  X,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { useIdentities, useRegisterIdentity } from "@/hooks/use-identities";
import type { AgentType } from "@/lib/types";

const agentTypes: { value: AgentType; label: string }[] = [
  { value: "langchain", label: "LangChain" },
  { value: "crewai", label: "CrewAI" },
  { value: "openai_agents", label: "OpenAI Agents" },
  { value: "custom", label: "Custom" },
];

function getAgentTypeLabel(type: string): string {
  return agentTypes.find((t) => t.value === type)?.label ?? type;
}

export default function IdentitiesPage() {
  const { data, isLoading } = useIdentities();
  const registerMutation = useRegisterIdentity();
  const [showRegister, setShowRegister] = useState(false);
  const [search, setSearch] = useState("");
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState<AgentType>("custom");
  const [registered, setRegistered] = useState<{
    id: string;
    chain_id: string;
  } | null>(null);

  const identities = data?.data ?? [];
  const filtered = search
    ? identities.filter(
        (i) =>
          i.name.toLowerCase().includes(search.toLowerCase()) ||
          i.id.toLowerCase().includes(search.toLowerCase())
      )
    : identities;

  const handleRegister = async () => {
    if (!newName.trim()) return;
    try {
      const result = await registerMutation.mutateAsync({
        name: newName.trim(),
        agent_type: newType,
      });
      setRegistered({ id: result.id, chain_id: result.chain_id });
      toast.success("Identity registered");
    } catch {
      toast.error("Failed to register identity");
    }
  };

  const closeModal = () => {
    setShowRegister(false);
    setNewName("");
    setNewType("custom");
    setRegistered(null);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            Agent Identities
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Persistent, verifiable identities for agents and systems
          </p>
        </div>
        <button
          onClick={() => setShowRegister(true)}
          className="flex items-center gap-2 rounded-lg bg-pruv-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-pruv-600 transition-colors"
        >
          <Plus size={16} />
          Register Identity
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]"
        />
        <input
          type="text"
          placeholder="Search by name or address..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-10 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-pruv-500 focus:outline-none focus:ring-1 focus:ring-pruv-500"
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] animate-pulse"
            />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <Fingerprint
            size={48}
            className="mx-auto mb-4 text-[var(--text-tertiary)]"
          />
          <p className="text-[var(--text-secondary)] text-sm">
            {search ? "No identities match your search." : "No identities registered yet."}
          </p>
          {!search && (
            <button
              onClick={() => setShowRegister(true)}
              className="mt-4 text-sm text-pruv-500 hover:text-pruv-400"
            >
              Register your first identity
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((identity, idx) => (
            <motion.div
              key={identity.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.03 }}
            >
              <Link
                href={`/identities/${identity.id}`}
                className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4 hover:border-pruv-500/40 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-pruv-500/10">
                    <Fingerprint size={20} className="text-pruv-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-[var(--text-primary)]">
                        {identity.name}
                      </span>
                      <span className="rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                        {getAgentTypeLabel(identity.agent_type)}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-xs text-[var(--text-tertiary)] font-mono">
                      <span>{identity.id.slice(0, 16)}...</span>
                      {identity.last_action_at && (
                        <span>
                          last active:{" "}
                          {formatDistanceToNow(new Date(identity.last_action_at), {
                            addSuffix: true,
                          })}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-[var(--text-secondary)]">
                    {identity.action_count} actions
                  </span>
                  <CheckCircle2
                    size={16}
                    className="text-pruv-500"
                  />
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}

      {/* Register Modal */}
      <AnimatePresence>
        {showRegister && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={closeModal}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xl"
            >
              {!registered ? (
                <>
                  <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                    Register New Identity
                  </h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                        Agent Name
                      </label>
                      <input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        placeholder="my-agent"
                        className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-pruv-500 focus:outline-none focus:ring-1 focus:ring-pruv-500"
                        autoFocus
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                        Agent Type
                      </label>
                      <select
                        value={newType}
                        onChange={(e) =>
                          setNewType(e.target.value as AgentType)
                        }
                        className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-primary)] focus:border-pruv-500 focus:outline-none focus:ring-1 focus:ring-pruv-500"
                      >
                        {agentTypes.map((t) => (
                          <option key={t.value} value={t.value}>
                            {t.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="mt-6 flex items-center justify-end gap-3">
                    <button
                      onClick={closeModal}
                      className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleRegister}
                      disabled={
                        !newName.trim() || registerMutation.isPending
                      }
                      className="rounded-lg bg-pruv-500 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-600 disabled:opacity-50 transition-colors"
                    >
                      {registerMutation.isPending
                        ? "Registering..."
                        : "Register"}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle2 size={20} className="text-pruv-500" />
                    <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                      Identity Registered
                    </h2>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-[var(--text-tertiary)] mb-1">
                        Identity Address
                      </label>
                      <div className="rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] p-3 font-mono text-sm text-[var(--text-primary)] break-all">
                        {registered.id}
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[var(--text-tertiary)] mb-1">
                        Code Snippet
                      </label>
                      <pre className="rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] p-3 font-mono text-xs text-[var(--text-secondary)] overflow-x-auto">
{`import pruv

# Record actions for this identity
pruv.identity.act("${registered.id}", "action_name", {"key": "value"})

# Verify the identity
result = pruv.identity.verify("${registered.id}")
print(result.message)`}
                      </pre>
                    </div>
                  </div>
                  <div className="mt-6 flex items-center justify-end gap-3">
                    <button
                      onClick={closeModal}
                      className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] transition-colors"
                    >
                      Close
                    </button>
                    <Link
                      href={`/identities/${registered.id}`}
                      className="rounded-lg bg-pruv-500 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-600 transition-colors"
                    >
                      View Identity
                    </Link>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
