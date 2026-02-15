"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Search, FileCheck } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { ReceiptCard } from "@/components/receipt-card";
import { useReceipts } from "@/hooks/use-receipts";
import type { ReceiptFilters, ReceiptStatus } from "@/lib/types";

export default function ReceiptsPage() {
  const [filters, setFilters] = useState<ReceiptFilters>({
    sort_by: "created_at",
    sort_order: "desc",
    page: 1,
    per_page: 20,
  });
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ReceiptStatus | "">("");

  const { data, isLoading } = useReceipts({
    ...filters,
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const receipts = data?.data ?? [];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        <Header title="receipts" />

        <main className="p-6 space-y-4">
          {/* Filters */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]"
              />
              <input
                type="text"
                placeholder="search receipts..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none focus:ring-1 focus:ring-pruv-500/20 transition-all"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value as ReceiptStatus | "")
              }
              className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2.5 text-sm text-[var(--text-secondary)] focus:border-pruv-500/50 focus:outline-none"
            >
              <option value="">all statuses</option>
              <option value="verified">verified</option>
              <option value="failed">failed</option>
              <option value="pending">pending</option>
              <option value="expired">expired</option>
            </select>
          </div>

          {/* Receipt grid */}
          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 animate-pulse"
                >
                  <div className="flex items-start gap-3">
                    <div className="h-10 w-10 rounded-lg bg-[var(--surface-tertiary)]" />
                    <div className="flex-1">
                      <div className="h-4 w-32 rounded bg-[var(--surface-tertiary)]" />
                      <div className="mt-2 h-3 w-20 rounded bg-[var(--surface-tertiary)]" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : receipts.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--surface-secondary)] border border-[var(--border)] mb-4">
                <FileCheck size={24} className="text-[var(--text-tertiary)]" />
              </div>
              <p className="text-sm text-[var(--text-secondary)]">
                no receipts yet
              </p>
              <p className="mt-1 text-xs text-[var(--text-tertiary)]">
                receipts are generated when chains are verified
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {receipts.map((receipt, i) => (
                <ReceiptCard key={receipt.id} receipt={receipt} index={i} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {data && data.total > 0 && (
            <div className="flex items-center justify-between pt-4 text-xs text-[var(--text-tertiary)]">
              <span>
                showing {receipts.length} of {data.total} receipts
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
    </div>
  );
}
