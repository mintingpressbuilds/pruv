"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import { shared } from "@/lib/api";
import type { Chain, Entry } from "@/lib/types";

interface SharedChainResult {
  chain: Chain;
  entries: Entry[];
  verified: boolean;
}

export const sharedChainKeys = {
  all: ["shared-chain"] as const,
  detail: (shareId: string) => [...sharedChainKeys.all, shareId] as const,
};

export function useSharedChain(
  shareId: string,
  options?: Partial<UseQueryOptions<SharedChainResult>>
) {
  return useQuery({
    queryKey: sharedChainKeys.detail(shareId),
    queryFn: () => shared.get(shareId),
    enabled: !!shareId,
    ...options,
  });
}
