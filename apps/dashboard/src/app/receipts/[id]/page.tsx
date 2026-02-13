"use client";

import { useParams } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { ReceiptDetailView } from "@/components/receipt-detail";
import { useReceipt, useExportReceiptPdf } from "@/hooks/use-receipts";

export default function ReceiptDetailPage() {
  const params = useParams();
  const receiptId = params.id as string;

  const { data: receipt, isLoading } = useReceipt(receiptId);
  const exportPdf = useExportReceiptPdf();

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-64">
        <Header
          title={`receipt ${receiptId.slice(0, 12)}...`}
          subtitle={receipt?.chain_name}
        />

        <main className="p-6">
          {isLoading ? (
            <div className="space-y-4">
              <div className="h-24 rounded-xl bg-[var(--surface-secondary)] animate-pulse border border-[var(--border)]" />
              <div className="grid grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-20 rounded-xl bg-[var(--surface-secondary)] animate-pulse border border-[var(--border)]"
                  />
                ))}
              </div>
              <div className="h-48 rounded-xl bg-[var(--surface-secondary)] animate-pulse border border-[var(--border)]" />
            </div>
          ) : receipt ? (
            <ReceiptDetailView
              receipt={receipt}
              onExportPdf={() => exportPdf.mutate(receiptId)}
              isExporting={exportPdf.isPending}
            />
          ) : (
            <div className="flex flex-col items-center py-16 text-center">
              <p className="text-sm text-[var(--text-secondary)]">
                receipt not found
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
