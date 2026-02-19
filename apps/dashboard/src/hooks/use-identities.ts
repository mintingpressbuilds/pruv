"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { identities } from "@/lib/api";
import type { AgentIdentity, IdentityVerification } from "@/lib/types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const identityKeys = {
  all: ["identities"] as const,
  lists: () => [...identityKeys.all, "list"] as const,
  details: () => [...identityKeys.all, "detail"] as const,
  detail: (id: string) => [...identityKeys.details(), id] as const,
  verification: (id: string) =>
    [...identityKeys.detail(id), "verification"] as const,
  history: (id: string) =>
    [...identityKeys.detail(id), "history"] as const,
};

// ─── Queries ─────────────────────────────────────────────────────────────────

export function useIdentities(
  options?: Partial<
    UseQueryOptions<{ data: AgentIdentity[]; total: number }>
  >
) {
  return useQuery({
    queryKey: identityKeys.lists(),
    queryFn: () => identities.list(),
    ...options,
  });
}

export function useIdentity(
  id: string,
  options?: Partial<UseQueryOptions<AgentIdentity>>
) {
  return useQuery({
    queryKey: identityKeys.detail(id),
    queryFn: () => identities.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useIdentityVerification(
  id: string,
  options?: Partial<UseQueryOptions<IdentityVerification>>
) {
  return useQuery({
    queryKey: identityKeys.verification(id),
    queryFn: () => identities.verify(id),
    enabled: !!id,
    ...options,
  });
}

export function useIdentityHistory(
  id: string,
  params?: { limit?: number; offset?: number },
  options?: Partial<UseQueryOptions<{ actions: unknown[]; total: number }>>
) {
  return useQuery({
    queryKey: identityKeys.history(id),
    queryFn: () => identities.history(id, params),
    enabled: !!id,
    ...options,
  });
}

// ─── Mutations ───────────────────────────────────────────────────────────────

export function useRegisterIdentity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      name: string;
      agent_type?: string;
      metadata?: Record<string, unknown>;
    }) => identities.register(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: identityKeys.lists() });
    },
  });
}

export function useRecordAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      action,
      data,
    }: {
      id: string;
      action: string;
      data?: Record<string, unknown>;
    }) => identities.act(id, { action, data }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: identityKeys.detail(variables.id),
      });
      queryClient.invalidateQueries({
        queryKey: identityKeys.history(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: identityKeys.lists() });
    },
  });
}
