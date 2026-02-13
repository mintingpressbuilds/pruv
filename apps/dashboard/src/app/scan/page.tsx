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
} from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { scans } from "@/lib/api";
import type { ScanResult, ScanFinding } from "@/lib/types";

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

export default function ScanPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [chainId, setChainId] = useState("");
  const [deepVerify, setDeepVerify] = useState(true);
  const [checkSignatures, setCheckSignatures] = useState(true);
  const [generateReceipt, setGenerateReceipt] = useState(true);
  const [dragOver, setDragOver] = useState(false);

  const handleScan = async (file?: File) => {
    setIsScanning(true);
    setResult(null);
    try {
      const scanResult = await scans.trigger({
        chain_id: chainId || undefined,
        file,
        options: {
          deep_verify: deepVerify,
          check_signatures: checkSignatures,
          generate_receipt: generateReceipt,
        },
      });
      setResult(scanResult);
    } catch {
      // error handled by API client
    } finally {
      setIsScanning(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleScan(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleScan(file);
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-64">
        <Header title="scan" subtitle="verify chain integrity" />

        <main className="p-6 space-y-6 max-w-3xl">
          {/* Scan by chain id */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-1">
              scan a chain
            </h3>
            <p className="text-xs text-[var(--text-tertiary)] mb-4">
              enter a chain id to verify its integrity, or upload a scan file
            </p>
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="chain id..."
                value={chainId}
                onChange={(e) => setChainId(e.target.value)}
                className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none focus:ring-1 focus:ring-pruv-500/20 font-mono"
              />
              <button
                onClick={() => handleScan()}
                disabled={isScanning || !chainId}
                className="flex items-center gap-2 rounded-lg bg-pruv-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-pruv-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isScanning ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <ScanSearch size={14} />
                )}
                scan
              </button>
            </div>

            {/* Options */}
            <div className="mt-4 flex items-center gap-6">
              <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={deepVerify}
                  onChange={(e) => setDeepVerify(e.target.checked)}
                  className="rounded border-[var(--border)] bg-[var(--surface)] text-pruv-600 focus:ring-pruv-500/20"
                />
                deep verify
              </label>
              <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={checkSignatures}
                  onChange={(e) => setCheckSignatures(e.target.checked)}
                  className="rounded border-[var(--border)] bg-[var(--surface)] text-pruv-600 focus:ring-pruv-500/20"
                />
                check signatures
              </label>
              <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={generateReceipt}
                  onChange={(e) => setGenerateReceipt(e.target.checked)}
                  className="rounded border-[var(--border)] bg-[var(--surface)] text-pruv-600 focus:ring-pruv-500/20"
                />
                generate receipt
              </label>
            </div>
          </div>

          {/* Upload area */}
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
              accept=".json"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload
              size={32}
              className={`mx-auto mb-3 ${dragOver ? "text-pruv-400" : "text-[var(--text-tertiary)]"}`}
            />
            <p className="text-sm text-[var(--text-secondary)]">
              drop a scan json file here, or click to browse
            </p>
            <p className="mt-1 text-xs text-[var(--text-tertiary)]">
              supports output from{" "}
              <code className="text-pruv-400">pruv scan --json-output</code>
            </p>
          </div>

          {/* CLI instructions */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
            <div className="flex items-center gap-2 mb-3">
              <Terminal size={14} className="text-pruv-400" />
              <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                cli usage
              </h3>
            </div>
            <div className="space-y-3">
              <div className="rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                <code className="text-xs text-pruv-400 font-mono">
                  pruv scan ./my-project --json-output &gt; scan.json
                </code>
              </div>
              <div className="rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)]">
                <code className="text-xs text-pruv-400 font-mono">
                  pruv upload ./my-project --api-key pv_live_...
                </code>
              </div>
            </div>
          </div>

          {/* Scan result */}
          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    {result.status === "completed" ? (
                      <Check size={16} className="text-green-400" />
                    ) : (
                      <Loader2 size={16} className="text-pruv-400 animate-spin" />
                    )}
                    <h3 className="text-sm font-medium text-[var(--text-primary)]">
                      scan {result.status}
                    </h3>
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
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
