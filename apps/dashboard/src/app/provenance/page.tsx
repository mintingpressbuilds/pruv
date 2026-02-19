"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileSearch,
  Plus,
  CheckCircle2,
  Search,
  X,
  Upload,
  Hash,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { useArtifacts, useRegisterOrigin } from "@/hooks/use-provenance";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";

export default function ProvenancePage() {
  const { data, isLoading } = useArtifacts();
  const originMutation = useRegisterOrigin();
  const [showRegister, setShowRegister] = useState(false);
  const [search, setSearch] = useState("");

  // Registration form state
  const [newName, setNewName] = useState("");
  const [newCreator, setNewCreator] = useState("");
  const [newContentType, setNewContentType] = useState(
    "application/octet-stream"
  );
  const [newHash, setNewHash] = useState("");
  const [hashMethod, setHashMethod] = useState<"file" | "manual">("file");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [registered, setRegistered] = useState<{
    id: string;
    content_hash: string;
  } | null>(null);

  const artifacts = data?.data ?? [];
  const filtered = search
    ? artifacts.filter(
        (a) =>
          a.name.toLowerCase().includes(search.toLowerCase()) ||
          a.id.toLowerCase().includes(search.toLowerCase()) ||
          a.creator.toLowerCase().includes(search.toLowerCase())
      )
    : artifacts;

  const handleFileHash = async (file: File) => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    const hashHex = Array.from(new Uint8Array(hashBuffer))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    setNewHash(hashHex);
    if (!newName) setNewName(file.name);
    if (!newContentType || newContentType === "application/octet-stream") {
      setNewContentType(file.type || "application/octet-stream");
    }
  };

  const handleRegister = async () => {
    if (!newName.trim() || !newCreator.trim() || !newHash.trim()) return;
    try {
      const result = await originMutation.mutateAsync({
        content_hash: newHash.trim(),
        name: newName.trim(),
        creator: newCreator.trim(),
        content_type: newContentType,
      });
      setRegistered({ id: result.id, content_hash: result.content_hash });
      toast.success("Artifact origin registered");
    } catch {
      toast.error("Failed to register artifact");
    }
  };

  const closeModal = () => {
    setShowRegister(false);
    setNewName("");
    setNewCreator("");
    setNewContentType("application/octet-stream");
    setNewHash("");
    setHashMethod("file");
    setRegistered(null);
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        <Header
          title="provenance"
          subtitle="Origin tracking and chain of custody for digital artifacts"
          actions={
            <button
              onClick={() => setShowRegister(true)}
              className="flex items-center gap-2 rounded-lg bg-pruv-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-pruv-600 transition-colors"
            >
              <Plus size={16} />
              Register Artifact
            </button>
          }
        />
    <div className="p-6 max-w-5xl mx-auto">

      {/* Search */}
      <div className="relative mb-4">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]"
        />
        <input
          type="text"
          placeholder="Search by name, address, or creator..."
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
          <FileSearch
            size={48}
            className="mx-auto mb-4 text-[var(--text-tertiary)]"
          />
          <p className="text-[var(--text-secondary)] text-sm">
            {search
              ? "No artifacts match your search."
              : "No artifacts registered yet."}
          </p>
          {!search && (
            <button
              onClick={() => setShowRegister(true)}
              className="mt-4 text-sm text-pruv-500 hover:text-pruv-400"
            >
              Register your first artifact
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((artifact, idx) => (
            <motion.div
              key={artifact.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.03 }}
            >
              <Link
                href={`/provenance/${artifact.id}`}
                className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4 hover:border-pruv-500/40 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-pruv-500/10">
                    <FileSearch size={20} className="text-pruv-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-[var(--text-primary)]">
                        {artifact.name}
                      </span>
                      <span className="rounded-full bg-[var(--surface-tertiary)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                        {artifact.content_type}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
                      <span className="font-mono">
                        {artifact.id.slice(0, 16)}...
                      </span>
                      <span>creator: {artifact.creator}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-[var(--text-secondary)]">
                    {artifact.transition_count === 0
                      ? "unmodified"
                      : `${artifact.transition_count} modification${artifact.transition_count > 1 ? "s" : ""}`}
                  </span>
                  <CheckCircle2 size={16} className="text-pruv-500" />
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
                    Register Artifact Origin
                  </h2>
                  <p className="text-xs text-[var(--text-tertiary)] mb-4">
                    Only the hash is stored — your content never leaves your
                    machine.
                  </p>
                  <div className="space-y-4">
                    {/* Hash method toggle */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => setHashMethod("file")}
                        className={`flex-1 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                          hashMethod === "file"
                            ? "border-pruv-500 bg-pruv-500/10 text-pruv-500"
                            : "border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)]"
                        }`}
                      >
                        <Upload size={14} />
                        Hash from file
                      </button>
                      <button
                        onClick={() => setHashMethod("manual")}
                        className={`flex-1 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                          hashMethod === "manual"
                            ? "border-pruv-500 bg-pruv-500/10 text-pruv-500"
                            : "border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)]"
                        }`}
                      >
                        <Hash size={14} />
                        Paste hash
                      </button>
                    </div>

                    {hashMethod === "file" ? (
                      <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                          File (hashed locally, never uploaded)
                        </label>
                        <input
                          ref={fileInputRef}
                          type="file"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleFileHash(file);
                          }}
                          className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] file:mr-3 file:rounded-md file:border-0 file:bg-pruv-500/10 file:px-3 file:py-1 file:text-sm file:text-pruv-500"
                        />
                        {newHash && (
                          <div className="mt-2 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] p-2 font-mono text-xs text-[var(--text-tertiary)] break-all">
                            SHA-256: {newHash}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                          Content Hash (SHA-256)
                        </label>
                        <input
                          type="text"
                          value={newHash}
                          onChange={(e) => setNewHash(e.target.value)}
                          placeholder="e.g. a3f8c2e1d4..."
                          className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-pruv-500 focus:outline-none focus:ring-1 focus:ring-pruv-500"
                        />
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                        Artifact Name
                      </label>
                      <input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        placeholder="contract-v1.pdf"
                        className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-pruv-500 focus:outline-none focus:ring-1 focus:ring-pruv-500"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                          Creator
                        </label>
                        <input
                          type="text"
                          value={newCreator}
                          onChange={(e) => setNewCreator(e.target.value)}
                          placeholder="alice@acme.com"
                          className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-pruv-500 focus:outline-none focus:ring-1 focus:ring-pruv-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                          Content Type
                        </label>
                        <input
                          type="text"
                          value={newContentType}
                          onChange={(e) => setNewContentType(e.target.value)}
                          placeholder="application/pdf"
                          className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-pruv-500 focus:outline-none focus:ring-1 focus:ring-pruv-500"
                        />
                      </div>
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
                        !newName.trim() ||
                        !newCreator.trim() ||
                        !newHash.trim() ||
                        originMutation.isPending
                      }
                      className="rounded-lg bg-pruv-500 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-600 disabled:opacity-50 transition-colors"
                    >
                      {originMutation.isPending
                        ? "Registering..."
                        : "Register Origin"}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle2 size={20} className="text-pruv-500" />
                    <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                      Artifact Registered
                    </h2>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-[var(--text-tertiary)] mb-1">
                        Artifact ID
                      </label>
                      <div className="rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] p-3 font-mono text-sm text-[var(--text-primary)] break-all">
                        {registered.id}
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[var(--text-tertiary)] mb-1">
                        Origin Hash
                      </label>
                      <div className="rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] p-3 font-mono text-xs text-[var(--text-secondary)] break-all">
                        {registered.content_hash}
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[var(--text-tertiary)] mb-1">
                        Code Snippet
                      </label>
                      <pre className="rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] p-3 font-mono text-xs text-[var(--text-secondary)] overflow-x-auto">
{`import pruv

# Record a modification
pruv.provenance.transition(
    "${registered.id}",
    content=updated_bytes,
    modifier="editor@acme.com",
    reason="Updated section 3"
)

# Verify provenance
result = pruv.provenance.verify("${registered.id}")
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
                      href={`/provenance/${registered.id}`}
                      className="rounded-lg bg-pruv-500 px-4 py-2 text-sm font-medium text-white hover:bg-pruv-600 transition-colors"
                    >
                      View Artifact
                    </Link>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
      </div>
    </div>
  );
}
