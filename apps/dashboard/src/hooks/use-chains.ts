"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { chains } from "@/lib/api";
import type {
  Chain,
  ChainFilters,
  EntryValidation,
  PaginatedResponse,
} from "@/lib/types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const chainKeys = {
  all: ["chains"] as const,
  lists: () => [...chainKeys.all, "list"] as const,
  list: (filters: ChainFilters) =>
    [...chainKeys.lists(), filters] as const,
  details: () => [...chainKeys.all, "detail"] as const,
  detail: (id: string) => [...chainKeys.details(), id] as const,
  verification: (id: string) =>
    [...chainKeys.detail(id), "verification"] as const,
};

// ─── Queries ─────────────────────────────────────────────────────────────────

export function useChains(
  filters: ChainFilters = {},
  options?: Partial<UseQueryOptions<PaginatedResponse<Chain>>>
) {
  return useQuery({
    queryKey: chainKeys.list(filters),
    queryFn: () => chains.list(filters),
    ...options,
  });
}

export function useChain(
  id: string,
  options?: Partial<UseQueryOptions<Chain>>
) {
  return useQuery({
    queryKey: chainKeys.detail(id),
    queryFn: () => chains.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useChainVerification(
  id: string,
  options?: Partial<UseQueryOptions<EntryValidation[]>>
) {
  return useQuery({
    queryKey: chainKeys.verification(id),
    queryFn: () => chains.verify(id),
    enabled: !!id,
    ...options,
  });
}

// ─── Mutations ───────────────────────────────────────────────────────────────

export function useCreateChain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      name: string;
      description?: string;
      tags?: string[];
    }) => chains.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chainKeys.lists() });
    },
  });
}

export function useUpdateChain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Pick<Chain, "name" | "description" | "tags">>;
    }) => chains.update(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: chainKeys.detail(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: chainKeys.lists() });
    },
  });
}

export function useDeleteChain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => chains.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chainKeys.lists() });
    },
  });
}
