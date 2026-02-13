"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { receipts } from "@/lib/api";
import type {
  Receipt,
  ReceiptFilters,
  PaginatedResponse,
} from "@/lib/types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const receiptKeys = {
  all: ["receipts"] as const,
  lists: () => [...receiptKeys.all, "list"] as const,
  list: (filters: ReceiptFilters) =>
    [...receiptKeys.lists(), filters] as const,
  details: () => [...receiptKeys.all, "detail"] as const,
  detail: (id: string) => [...receiptKeys.details(), id] as const,
};

// ─── Queries ─────────────────────────────────────────────────────────────────

export function useReceipts(
  filters: ReceiptFilters = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<Receipt>>>
) {
  return useQuery({
    queryKey: receiptKeys.list(filters),
    queryFn: () => receipts.list(filters),
    ...options,
  });
}

export function useReceipt(
  id: string,
  options?: Partial<UseQueryOptions<Receipt>>
) {
  return useQuery({
    queryKey: receiptKeys.detail(id),
    queryFn: () => receipts.get(id),
    enabled: !!id,
    ...options,
  });
}

// ─── Mutations ───────────────────────────────────────────────────────────────

export function useCreateReceipt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (chainId: string) => receipts.create(chainId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: receiptKeys.lists() });
    },
  });
}

export function useExportReceiptPdf() {
  return useMutation({
    mutationFn: async (id: string) => {
      const blob = await receipts.getPdf(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pruv-receipt-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
  });
}
