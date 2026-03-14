import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useParams } from "next/navigation";
import SharedChainPage from "@/app/shared/[shareId]/page";
import { sha256, computeXY } from "@/lib/verify-chain";
import type { Entry, Chain } from "@/lib/types";

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

function renderPage() {
  return render(<SharedChainPage />, { wrapper: createWrapper() });
}

const TIMESTAMP = "2024-06-15T10:30:00.000Z";

async function makeValidEntries(): Promise<Entry[]> {
  const y0 = await sha256("state-1");
  const xy0 = await computeXY("GENESIS", "init", y0, TIMESTAMP);

  const y1 = await sha256("state-2");
  const xy1 = await computeXY(y0, "update", y1, TIMESTAMP);

  return [
    {
      index: 0,
      chain_id: "ch_test",
      x: "GENESIS",
      y: y0,
      xy_proof: xy0,
      timestamp: TIMESTAMP,
      actor: "agent-1",
      action: "init",
      signed: false,
      metadata: {},
    },
    {
      index: 1,
      chain_id: "ch_test",
      x: y0,
      y: y1,
      xy_proof: xy1,
      timestamp: TIMESTAMP,
      actor: "agent-1",
      action: "update",
      signed: true,
      metadata: {},
    },
  ];
}

const MOCK_CHAIN: Chain = {
  id: "ch_test",
  name: "deploy-pipeline",
  chain_type: "operations",
  created_at: "2024-06-15T10:00:00.000Z",
  updated_at: "2024-06-15T10:30:00.000Z",
  entry_count: 2,
  status: "valid",
  owner_id: "user_1",
  tags: [],
  metadata: {},
};

// ─── Tests ────────────────────────────────────────────────────────────────

describe("SharedChainPage", () => {
  beforeEach(() => {
    mockGet.mockReset();
    vi.mocked(useParams).mockReturnValue({ shareId: "abc123def456" });
  });

  it("shows loading state initially", () => {
    mockGet.mockReturnValue(new Promise(() => {})); // never resolves
    renderPage();
    expect(screen.getByText("loading shared chain...")).toBeInTheDocument();
  });

  it("shows not found when API returns 404", async () => {
    mockGet.mockRejectedValue({ status: 404, message: "Not found" });
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("shared chain not found")).toBeInTheDocument();
    });
    expect(
      screen.getByText(/this link may have expired/)
    ).toBeInTheDocument();
  });

  it("shows connection error with retry button for non-404 errors", async () => {
    mockGet.mockRejectedValue({ status: 500, message: "Server error" });
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText("unable to load shared chain")
      ).toBeInTheDocument();
    });
    expect(
      screen.getByText(/could not reach the verification server/)
    ).toBeInTheDocument();
    expect(screen.getByText("retry")).toBeInTheDocument();
  });

  it("renders chain name and metadata on success", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("deploy-pipeline")).toBeInTheDocument();
    });

    expect(screen.getByText("chain verified")).toBeInTheDocument();
    expect(screen.getByText("operations")).toBeInTheDocument();
    expect(screen.getByText("2 entries")).toBeInTheDocument();
  });

  it("shows chain broken when server verification fails", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("chain broken")).toBeInTheDocument();
    });
  });

  it("renders entry timeline with all entries", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("init")).toBeInTheDocument();
    });
    expect(screen.getByText("update")).toBeInTheDocument();
    expect(screen.getByText("#0")).toBeInTheDocument();
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText(/chain origin/)).toBeInTheDocument();
  });

  it("expands entry detail on click", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("init")).toBeInTheDocument();
    });

    // Click entry to expand
    await user.click(screen.getByText("init"));

    // Should show hash details
    expect(screen.getByText("x (before)")).toBeInTheDocument();
    expect(screen.getByText("y (after)")).toBeInTheDocument();
    expect(screen.getByText("xy proof")).toBeInTheDocument();
    expect(screen.getByText("agent-1")).toBeInTheDocument();
  });

  it("shows signed badge for signed entries", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("update")).toBeInTheDocument();
    });

    // Entry 1 is signed — expand it
    await user.click(screen.getByText("update"));
    expect(screen.getByText("signed")).toBeInTheDocument();
  });

  it("collapses entry on second click", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("init")).toBeInTheDocument();
    });

    await user.click(screen.getByText("init"));
    expect(screen.getByText("x (before)")).toBeInTheDocument();

    await user.click(screen.getByText("init"));
    expect(screen.queryByText("x (before)")).not.toBeInTheDocument();
  });

  it("runs client-side verification and shows success", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("verify locally")).toBeInTheDocument();
    });

    await user.click(screen.getByText("verify locally"));

    await waitFor(() => {
      expect(
        screen.getByText(/all 2 entries verified/)
      ).toBeInTheDocument();
    });
  });

  it("runs client-side verification and shows failure for tampered chain", async () => {
    const entries = await makeValidEntries();
    // Tamper entry[1] xy proof
    entries[1] = {
      ...entries[1],
      xy_proof: "xy_0000000000000000000000000000000000000000000000000000000000000000",
    };

    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true, // server said OK but client catches it
    });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("verify locally")).toBeInTheDocument();
    });

    await user.click(screen.getByText("verify locally"));

    await waitFor(() => {
      expect(
        screen.getByText(/chain broken/)
      ).toBeInTheDocument();
    });
  });

  it("renders chain boundaries section", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("chain boundaries")).toBeInTheDocument();
    });

    expect(screen.getByText("root x")).toBeInTheDocument();
    expect(screen.getByText("head y")).toBeInTheDocument();
    expect(screen.getByText("root proof")).toBeInTheDocument();
    expect(screen.getByText("head proof")).toBeInTheDocument();
  });

  it("renders header with pruv branding and what is pruv link", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("pruv")).toBeInTheDocument();
    });

    expect(screen.getByText("shared chain")).toBeInTheDocument();
    expect(screen.getByText("what is pruv?")).toBeInTheDocument();
  });

  it("renders get pruv CTA", async () => {
    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("get pruv")).toBeInTheDocument();
    });

    const ctaLink = screen.getByText("get pruv").closest("a");
    expect(ctaLink).toHaveAttribute("href", "https://pruv.dev");
    expect(ctaLink).toHaveAttribute("target", "_blank");
  });

  it("copies hash to clipboard when copy button clicked", async () => {
    const writeTextSpy = vi.spyOn(navigator.clipboard, "writeText");

    const entries = await makeValidEntries();
    mockGet.mockResolvedValue({
      chain: MOCK_CHAIN,
      entries,
      verified: true,
    });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("chain boundaries")).toBeInTheDocument();
    });

    // There are copy buttons next to hash values — get the first one in chain boundaries
    const boundaries = screen.getByText("chain boundaries").closest("div")!;
    const copyButtons = boundaries.querySelectorAll("button");
    expect(copyButtons.length).toBeGreaterThan(0);

    await user.click(copyButtons[0]);
    expect(writeTextSpy).toHaveBeenCalled();

    writeTextSpy.mockRestore();
  });

  it("passes share ID from URL params to API", async () => {
    vi.mocked(useParams).mockReturnValue({ shareId: "my_share_id" });
    mockGet.mockResolvedValue(
      new Promise(() => {}) // never resolves, we just check the call
    );

    renderPage();

    expect(mockGet).toHaveBeenCalledWith("my_share_id");
  });
});
