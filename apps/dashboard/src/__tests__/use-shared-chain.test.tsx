import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useSharedChain, sharedChainKeys } from "@/hooks/use-shared-chain";

// ─── Mock API ─────────────────────────────────────────────────────────────

const mockGet = vi.fn();

vi.mock("@/lib/api", () => ({
  shared: {
    get: (...args: unknown[]) => mockGet(...args),
  },
}));

// ─── Helpers ──────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

const MOCK_CHAIN_DATA = {
  chain: {
    id: "ch_test123",
    name: "test chain",
    chain_type: "operations" as const,
    created_at: "2024-01-01T00:00:00.000Z",
    updated_at: "2024-01-01T00:00:00.000Z",
    entry_count: 2,
    status: "valid" as const,
    owner_id: "user_1",
    tags: [],
    metadata: {},
  },
  entries: [
    {
      index: 0,
      chain_id: "ch_test123",
      x: "GENESIS",
      y: "abc123",
      xy_proof: "xy_def456",
      timestamp: "2024-01-01T00:00:00.000Z",
      actor: "system",
      action: "init",
      signed: false,
      metadata: {},
    },
    {
      index: 1,
      chain_id: "ch_test123",
      x: "abc123",
      y: "ghi789",
      xy_proof: "xy_jkl012",
      timestamp: "2024-01-01T00:01:00.000Z",
      actor: "system",
      action: "update",
      signed: false,
      metadata: {},
    },
  ],
  verified: true,
};

// ─── Tests ────────────────────────────────────────────────────────────────

describe("sharedChainKeys", () => {
  it("generates correct query keys", () => {
    expect(sharedChainKeys.all).toEqual(["shared-chain"]);
    expect(sharedChainKeys.detail("abc123")).toEqual([
      "shared-chain",
      "abc123",
    ]);
  });

  it("generates unique keys for different share IDs", () => {
    const keyA = sharedChainKeys.detail("aaa");
    const keyB = sharedChainKeys.detail("bbb");
    expect(keyA).not.toEqual(keyB);
  });
});

describe("useSharedChain", () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it("fetches shared chain data", async () => {
    mockGet.mockResolvedValue(MOCK_CHAIN_DATA);

    const { result } = renderHook(() => useSharedChain("share_abc"), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith("share_abc");
    expect(result.current.data?.chain.name).toBe("test chain");
    expect(result.current.data?.entries).toHaveLength(2);
    expect(result.current.data?.verified).toBe(true);
  });

  it("is disabled when shareId is empty", () => {
    mockGet.mockResolvedValue(MOCK_CHAIN_DATA);

    const { result } = renderHook(() => useSharedChain(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGet).not.toHaveBeenCalled();
  });

  it("handles API errors without retrying", async () => {
    mockGet.mockRejectedValue({
      error: "not_found",
      message: "Shared chain not found",
      status: 404,
    });

    const { result } = renderHook(() => useSharedChain("bad_id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
    // Should only call once (no retries)
    expect(mockGet).toHaveBeenCalledTimes(1);
  });

  it("returns unverified chain data when server says broken", async () => {
    mockGet.mockResolvedValue({ ...MOCK_CHAIN_DATA, verified: false });

    const { result } = renderHook(() => useSharedChain("broken_share"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.verified).toBe(false);
  });

  it("passes through custom query options", async () => {
    mockGet.mockResolvedValue(MOCK_CHAIN_DATA);

    const { result } = renderHook(
      () =>
        useSharedChain("share_abc", {
          staleTime: 60_000,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toBeTruthy();
  });
});
