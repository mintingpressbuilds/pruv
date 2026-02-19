"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { provenanceApi } from "@/lib/api";
import type { ProvenanceArtifact, ProvenanceVerification } from "@/lib/types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const provenanceKeys = {
  all: ["provenance"] as const,
  lists: () => [...provenanceKeys.all, "list"] as const,
  details: () => [...provenanceKeys.all, "detail"] as const,
  detail: (id: string) => [...provenanceKeys.details(), id] as const,
  verification: (id: string) =>
    [...provenanceKeys.detail(id), "verification"] as const,
  history: (id: string) =>
    [...provenanceKeys.detail(id), "history"] as const,
};

// ─── Queries ─────────────────────────────────────────────────────────────────

export function useArtifacts(
  options?: Partial<
    UseQueryOptions<{ data: ProvenanceArtifact[]; total: number }>
  >
) {
  return useQuery({
    queryKey: provenanceKeys.lists(),
    queryFn: () => provenanceApi.list(),
    ...options,
  });
}

export function useArtifact(
  id: string,
  options?: Partial<UseQueryOptions<ProvenanceArtifact>>
) {
  return useQuery({
    queryKey: provenanceKeys.detail(id),
    queryFn: () => provenanceApi.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useProvenanceVerification(
  id: string,
  options?: Partial<UseQueryOptions<ProvenanceVerification>>
) {
  return useQuery({
    queryKey: provenanceKeys.verification(id),
    queryFn: () => provenanceApi.verify(id),
    enabled: !!id,
    ...options,
  });
}

export function useProvenanceHistory(
  id: string,
  params?: { limit?: number; offset?: number },
  options?: Partial<UseQueryOptions<{ entries: unknown[]; total: number }>>
) {
  return useQuery({
    queryKey: provenanceKeys.history(id),
    queryFn: () => provenanceApi.history(id, params),
    enabled: !!id,
    ...options,
  });
}

// ─── Mutations ───────────────────────────────────────────────────────────────

export function useRegisterOrigin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      content_hash: string;
      name: string;
      creator: string;
      content_type?: string;
      metadata?: Record<string, unknown>;
    }) => provenanceApi.origin(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: provenanceKeys.lists() });
    },
  });
}

export function useRecordTransition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      ...data
    }: {
      id: string;
      new_hash: string;
      modifier: string;
      reason?: string;
      metadata?: Record<string, unknown>;
    }) => provenanceApi.transition(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: provenanceKeys.detail(variables.id),
      });
      queryClient.invalidateQueries({
        queryKey: provenanceKeys.history(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: provenanceKeys.lists() });
    },
  });
}
