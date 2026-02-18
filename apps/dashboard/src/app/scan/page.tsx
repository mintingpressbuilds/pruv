"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  ScanSearch,
  Loader2,
  Check,
  AlertTriangle,
  Info,
  Terminal,
  FileText,
  XCircle,
  CheckCircle2,
  Copy,
  Globe,
  Link,
  ArrowRight,
  Archive,
} from "lucide-react";
import { toast } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { scans } from "@/lib/api";
import type { ScanResult, ScanFinding, ScanEntry } from "@/lib/types";

const severityConfig: Record<
  ScanFinding["severity"],
  { icon: React.ReactNode; color: string }
> = {
  critical: {
    icon: <AlertTriangle size={14} />,
    color: "text-red-400 bg-red-500/10 border-red-500/20",
  },
  warning: {
    icon: <AlertTriangle size={14} />,
    color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  },
  info: {
    icon: <Info size={14} />,
    color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  },
};

const FILE_TYPE_COLORS: Record<string, string> = {
  py: "text-yellow-400",
  js: "text-yellow-300",
  ts: "text-blue-400",
  tsx: "text-blue-400",
  jsx: "text-yellow-300",
  go: "text-cyan-400",
  rs: "text-orange-400",
  rb: "text-red-400",
  java: "text-orange-300",
  json: "text-green-400",
  yaml: "text-pink-400",
  yml: "text-pink-400",
  md: "text-[var(--text-secondary)]",
  html: "text-orange-400",
  css: "text-blue-300",
  sql: "text-purple-400",
  sh: "text-green-300",
  toml: "text-gray-400",
  url: "text-pruv-400",
};

function isGitHubUrl(url: string): boolean {
  return /^(?:https?:\/\/)?github\.com\/[\w.-]+\/[\w.-]+/.test(url.trim());
}

function formatSize(bytes: number): string {
  if (bytes === 0) return "";
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export default function ScanPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanSource, setScanSource] = useState<string>("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [chainId, setChainId] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const resetResult = () => {
    setResult(null);
    setScanSource("");
  };

  // ── URL scan (GitHub or generic) ──
  const handleUrlScan = async () => {
    const url = urlInput.trim();
    if (!url) return;

    setIsScanning(true);
    resetResult();
    setScanSource(isGitHubUrl(url) ? "github" : "url");

    try {
      let scanResult: ScanResult;
      if (isGitHubUrl(url)) {
        scanResult = await scans.scanGitHub(url);
      } else {
        scanResult = await scans.scanUrl(url);
      }
      setResult(scanResult);
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail || "Scan failed";
      toast.error(detail);
    } finally {
      setIsScanning(false);
    }
  };

  // ── File drop (ZIP or JSON) ──
  const handleFileScan = async (file: File) => {
    setIsScanning(true);
    resetResult();

    const isZip = file.name.endsWith(".zip") || file.type === "application/zip";
    setScanSource(isZip ? "zip" : "json");

    try {
      let scanResult: ScanResult;
      if (isZip) {
        scanResult = await scans.uploadZip(file);
      } else {
        scanResult = await scans.trigger({ file });
      }
      setResult(scanResult);
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail || "Scan failed";
      toast.error(detail);
    } finally {
      setIsScanning(false);
    }
  };

  // ── Chain ID verify ──
  const handleChainVerify = async () => {
    if (!chainId.trim()) return;

    setIsScanning(true);
    resetResult();
    setScanSource("chain");

    try {
      const scanResult = await scans.trigger({
        chain_id: chainId.trim(),
        options: {
          deep_verify: true,
          check_signatures: true,
          generate_receipt: true,
        },
      });
      setResult(scanResult);
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail || "Verification failed";
      toast.error(detail);
    } finally {
      setIsScanning(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileScan(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileScan(file);
  };

  const handleCopyCmd = (cmd: string, label: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(label);
    toast.success("copied");
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const entries = result?.entries ?? [];
  const verifiedCount = entries.filter((e) => e.verified).length;
  const brokenCount = entries.filter((e) => !e.verified).length;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        <Header title="scan & verify" subtitle="scan files, repos, or URLs" />

        <main className="p-6 space-y-6 max-w-3xl">
          {/* ── 1. URL input (GitHub or any URL) ── */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
            <div className="flex items-center gap-2 mb-1">
              <Globe size={14} className="text-pruv-400" />
              <h3 className="text-sm font-medium text-[var(--text-primary)]">
                paste a GitHub URL or any URL
              </h3>
            </div>
            <p className="text-xs text-[var(--text-tertiary)] mb-4">
              scan a public GitHub repo or hash any webpage
            </p>
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="https://github.com/user/repo"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleUrlScan()}
                disabled={isScanning}
                className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none focus:ring-1 focus:ring-pruv-500/20 font-mono"
              />
              <button
                onClick={handleUrlScan}
                disabled={isScanning || !urlInput.trim()}
                className="flex items-center gap-2 rounded-lg bg-pruv-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-pruv-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isScanning && scanSource !== "zip" && scanSource !== "json" && scanSource !== "chain" ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <ArrowRight size={14} />
                )}
                scan
              </button>
            </div>
            <p className="mt-2 text-[10px] text-[var(--text-tertiary)]">
              accepts: github.com/user/repo · https://github.com/user/repo/tree/branch · any URL
            </p>
          </div>

          {/* ── Divider ── */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-[var(--border)]" />
            <span className="text-xs text-[var(--text-tertiary)]">or</span>
            <div className="flex-1 h-px bg-[var(--border)]" />
          </div>

          {/* ── 2. Drag-and-drop zone (ZIP or JSON) ── */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`rounded-xl border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-200 ${
              dragOver
                ? "border-pruv-500 bg-pruv-500/5"
                : "border-[var(--border)] bg-[var(--surface-secondary)] hover:border-[var(--border-secondary)]"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.zip"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="flex items-center justify-center gap-3 mb-3">
              <Archive
                size={28}
                className={dragOver ? "text-pruv-400" : "text-[var(--text-tertiary)]"}
              />
              <Upload
                size={28}
                className={dragOver ? "text-pruv-400" : "text-[var(--text-tertiary)]"}
              />
            </div>
            <p className="text-sm text-[var(--text-secondary)]">
              drop a <span className="text-pruv-400 font-mono">.zip</span> or{" "}
              <span className="text-pruv-400 font-mono">.json</span> file here, or click to browse
            </p>
            <p className="mt-1 text-xs text-[var(--text-tertiary)]">
              ZIP files are extracted and every file is hashed into a chain
            </p>
          </div>

          {/* ── Divider ── */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-[var(--border)]" />
            <span className="text-xs text-[var(--text-tertiary)]">or</span>
            <div className="flex-1 h-px bg-[var(--border)]" />
          </div>

          {/* ── 3. Chain ID verify ── */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
            <div className="flex items-center gap-2 mb-1">
              <Link size={14} className="text-pruv-400" />
              <h3 className="text-sm font-medium text-[var(--text-primary)]">
                enter a chain ID to verify
              </h3>
            </div>
            <p className="text-xs text-[var(--text-tertiary)] mb-4">
              verify the integrity of an existing chain
            </p>
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="ch_a3f8c2e1"
                value={chainId}
                onChange={(e) => setChainId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleChainVerify()}
                disabled={isScanning}
                className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none focus:ring-1 focus:ring-pruv-500/20 font-mono"
              />
              <button
                onClick={handleChainVerify}
                disabled={isScanning || !chainId.trim()}
                className="flex items-center gap-2 rounded-lg bg-pruv-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-pruv-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isScanning && scanSource === "chain" ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <ScanSearch size={14} />
                )}
                verify
              </button>
            </div>
          </div>

          {/* ── CLI usage ── */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
            <div className="flex items-center gap-2 mb-3">
              <Terminal size={14} className="text-pruv-400" />
              <h3 className="text-sm font-medium text-[var(--text-primary)]">
                CLI usage
              </h3>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                <code className="text-xs text-pruv-400 font-mono">
                  pip install pruv
                </code>
                <button
                  onClick={() => handleCopyCmd("pip install pruv", "install")}
                  className="text-[var(--text-tertiary)] hover:text-pruv-400 transition-colors"
                >
                  {copiedCmd === "install" ? <Check size={12} /> : <Copy size={12} />}
                </button>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                <code className="text-xs text-pruv-400 font-mono">
                  pruv scan ./my-project --json-output &gt; scan.json
                </code>
                <button
                  onClick={() => handleCopyCmd("pruv scan ./my-project --json-output > scan.json", "scan")}
                  className="text-[var(--text-tertiary)] hover:text-pruv-400 transition-colors"
                >
                  {copiedCmd === "scan" ? <Check size={12} /> : <Copy size={12} />}
                </button>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                <code className="text-xs text-pruv-400 font-mono">
                  pruv upload scan.json --api-key pv_live_xxx
                </code>
                <button
                  onClick={() => handleCopyCmd("pruv upload scan.json --api-key pv_live_xxx", "upload")}
                  className="text-[var(--text-tertiary)] hover:text-pruv-400 transition-colors"
                >
                  {copiedCmd === "upload" ? <Check size={12} /> : <Copy size={12} />}
                </button>
              </div>
            </div>
          </div>

          {/* ── Loading state ── */}
          <AnimatePresence>
            {isScanning && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-8 text-center"
              >
                <Loader2 size={24} className="mx-auto mb-3 text-pruv-400 animate-spin" />
                <p className="text-sm text-[var(--text-secondary)]">
                  {scanSource === "github" && "downloading and scanning repository..."}
                  {scanSource === "zip" && "extracting and scanning files..."}
                  {scanSource === "url" && "fetching and hashing page..."}
                  {scanSource === "json" && "verifying chain..."}
                  {scanSource === "chain" && "verifying chain integrity..."}
                  {!scanSource && "scanning..."}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Scan result ── */}
          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                {/* Summary + findings */}
                <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      {result.findings.filter(f => f.severity === "critical").length === 0 ? (
                        <CheckCircle2 size={16} className="text-green-400" />
                      ) : (
                        <XCircle size={16} className="text-red-400" />
                      )}
                      <h3 className="text-sm font-medium text-[var(--text-primary)]">
                        scan {result.status}
                      </h3>
                      {result.source && (
                        <span className="text-[10px] text-[var(--text-tertiary)] font-mono px-2 py-0.5 rounded bg-[var(--surface)] border border-[var(--border)]">
                          {result.source}
                        </span>
                      )}
                    </div>
                    {result.receipt_id && (
                      <a
                        href={`/receipts/${result.receipt_id}`}
                        className="text-xs text-pruv-400 hover:text-pruv-300"
                      >
                        view receipt
                      </a>
                    )}
                  </div>

                  {/* Summary bar */}
                  {result.summary && (
                    <div className="flex items-center gap-3 mb-4 rounded-lg bg-[var(--surface)] border border-[var(--border)] px-4 py-3">
                      <FileText size={14} className="text-[var(--text-tertiary)]" />
                      <span className="text-xs text-[var(--text-secondary)]">
                        {result.summary}
                      </span>
                    </div>
                  )}

                  {/* Legacy summary bar for non-entry results */}
                  {!result.summary && entries.length > 0 && (
                    <div className="flex items-center gap-3 mb-4 rounded-lg bg-[var(--surface)] border border-[var(--border)] px-4 py-3">
                      <FileText size={14} className="text-[var(--text-tertiary)]" />
                      <span className="text-xs text-[var(--text-secondary)]">
                        {entries.length} files scanned
                      </span>
                      <span className="text-[var(--border)]">|</span>
                      {brokenCount === 0 ? (
                        <span className="flex items-center gap-1 text-xs text-green-400">
                          <CheckCircle2 size={12} />
                          all verified
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-red-400">
                          <XCircle size={12} />
                          {brokenCount} integrity failure{brokenCount !== 1 ? "s" : ""}
                        </span>
                      )}
                    </div>
                  )}

                  {result.findings.length > 0 ? (
                    <div className="space-y-2">
                      {result.findings.map((finding, i) => {
                        const config = severityConfig[finding.severity];
                        return (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -5 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className={`flex items-start gap-3 rounded-lg border p-3 ${config.color}`}
                          >
                            {config.icon}
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium">
                                  {finding.type}
                                </span>
                                {finding.entry_index !== undefined && (
                                  <span className="text-[10px] font-mono opacity-70">
                                    entry #{finding.entry_index}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs opacity-80 mt-0.5">
                                {finding.message}
                              </p>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-sm text-green-400">
                      <Check size={14} />
                      no issues found — chain integrity verified
                    </div>
                  )}
                </div>

                {/* File timeline */}
                {entries.length > 0 && (
                  <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
                    <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3">
                      file timeline
                    </h3>
                    <div className="space-y-0.5">
                      {entries.map((entry, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -5 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.015 }}
                          className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-[var(--surface)] transition-colors group"
                        >
                          {/* Verification icon */}
                          {entry.verified ? (
                            <CheckCircle2 size={14} className="shrink-0 text-green-400" />
                          ) : (
                            <XCircle size={14} className="shrink-0 text-red-400" />
                          )}

                          {/* Chain position */}
                          <span className="text-xs text-[var(--text-tertiary)] font-mono w-8 shrink-0">
                            #{entry.index}
                          </span>

                          {/* File type badge */}
                          {entry.file_type && (
                            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--surface)] border border-[var(--border)] shrink-0 ${FILE_TYPE_COLORS[entry.file_type] || "text-[var(--text-tertiary)]"}`}>
                              {entry.file_type}
                            </span>
                          )}

                          {/* File path */}
                          <span className="text-xs text-[var(--text-primary)] font-mono truncate flex-1">
                            {entry.path}
                          </span>

                          {/* File size */}
                          {entry.size > 0 && (
                            <span className="text-[10px] text-[var(--text-tertiary)] shrink-0 hidden group-hover:inline">
                              {formatSize(entry.size)}
                            </span>
                          )}

                          {/* Hash */}
                          <span className="text-[10px] text-[var(--text-tertiary)] font-mono shrink-0">
                            {entry.hash.slice(0, 12)}...
                          </span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
