"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { checkpoints } from "@/lib/api";
import { chainKeys } from "./use-chains";
import { entryKeys } from "./use-entries";
import type {
  Checkpoint,
  CheckpointPreview,
  CheckpointRestoreResult,
} from "@/lib/types";

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const checkpointKeys = {
  all: ["checkpoints"] as const,
  lists: () => [...checkpointKeys.all, "list"] as const,
  list: (chainId: string) => [...checkpointKeys.lists(), chainId] as const,
  preview: (chainId: string, checkpointId: string) =>
    [...checkpointKeys.all, "preview", chainId, checkpointId] as const,
};

// ─── Queries ─────────────────────────────────────────────────────────────────

export function useCheckpoints(
  chainId: string,
  options?: Partial<UseQueryOptions<Checkpoint[]>>
) {
  return useQuery({
    queryKey: checkpointKeys.list(chainId),
    queryFn: () => checkpoints.list(chainId),
    enabled: !!chainId,
    ...options,
  });
}

export function useCheckpointPreview(
  chainId: string,
  checkpointId: string,
  options?: Partial<UseQueryOptions<CheckpointPreview>>
) {
  return useQuery({
    queryKey: checkpointKeys.preview(chainId, checkpointId),
    queryFn: () => checkpoints.preview(chainId, checkpointId),
    enabled: !!chainId && !!checkpointId,
    ...options,
  });
}

// ─── Mutations ───────────────────────────────────────────────────────────────

export function useCreateCheckpoint(chainId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => checkpoints.create(chainId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: checkpointKeys.list(chainId),
      });
    },
  });
}

export function useRestoreCheckpoint(chainId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (checkpointId: string) =>
      checkpoints.restore(chainId, checkpointId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: checkpointKeys.list(chainId),
      });
      queryClient.invalidateQueries({
        queryKey: chainKeys.detail(chainId),
      });
      queryClient.invalidateQueries({
        queryKey: entryKeys.lists(),
      });
    },
  });
}
