"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { entries } from "@/lib/api";
import { chainKeys } from "./use-chains";
import type {
  Entry,
  EntryValidation,
  PaginatedResponse,
} from "@/lib/types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const entryKeys = {
  all: ["entries"] as const,
  lists: () => [...entryKeys.all, "list"] as const,
  list: (chainId: string, params?: { page?: number; per_page?: number }) =>
    [...entryKeys.lists(), chainId, params] as const,
  details: () => [...entryKeys.all, "detail"] as const,
  detail: (chainId: string, index: number) =>
    [...entryKeys.details(), chainId, index] as const,
  validation: (chainId: string, index: number) =>
    [...entryKeys.detail(chainId, index), "validation"] as const,
};

// ─── Queries ─────────────────────────────────────────────────────────────────

export function useEntries(
  chainId: string,
  params: { page?: number; per_page?: number } = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<Entry>>>
) {
  return useQuery({
    queryKey: entryKeys.list(chainId, params),
    queryFn: () => entries.list(chainId, params),
    enabled: !!chainId,
    ...options,
  });
}

export function useEntry(
  chainId: string,
  index: number,
  options?: Partial<UseQueryOptions<Entry>>
) {
  return useQuery({
    queryKey: entryKeys.detail(chainId, index),
    queryFn: () => entries.get(chainId, index),
    enabled: !!chainId && index >= 0,
    ...options,
  });
}

export function useEntryValidation(
  chainId: string,
  index: number,
  options?: Partial<UseQueryOptions<EntryValidation>>
) {
  return useQuery({
    queryKey: entryKeys.validation(chainId, index),
    queryFn: () => entries.validate(chainId, index),
    enabled: !!chainId && index >= 0,
    ...options,
  });
}

// ─── Mutations ───────────────────────────────────────────────────────────────

export function useCreateEntry(chainId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      y: string;
      action: string;
      metadata?: Record<string, unknown>;
    }) => entries.create(chainId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: entryKeys.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: chainKeys.detail(chainId),
      });
    },
  });
}

export function useUndoEntry(chainId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => entries.undo(chainId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: entryKeys.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: chainKeys.detail(chainId),
      });
    },
  });
}
