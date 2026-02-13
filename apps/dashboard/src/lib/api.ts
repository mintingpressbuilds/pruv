import type {
  Chain,
  Entry,
  EntryValidation,
  Receipt,
  PaginatedResponse,
  ApiError,
  ChainFilters,
  ReceiptFilters,
  DashboardStats,
  ApiKey,
  ApiKeyCreateResponse,
  ApiKeyScope,
  TeamMember,
  TeamInvite,
  TeamRole,
  BillingSubscription,
  BillingUsage,
  BillingPlan,
  ScanRequest,
  ScanResult,
  User,
} from "./types";

// ─── Config ──────────────────────────────────────────────────────────────────

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://api.pruv.dev";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("pruv_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...options.headers,
  };

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error: ApiError = await res.json().catch(() => ({
      error: "unknown",
      message: res.statusText,
      status: res.status,
    }));
    throw error;
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

function buildQueryString(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      if (Array.isArray(value)) {
        value.forEach((v) => searchParams.append(key, String(v)));
      } else {
        searchParams.set(key, String(value));
      }
    }
  }
  const qs = searchParams.toString();
  return qs ? `?${qs}` : "";
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export const auth = {
  signInWithGitHub(): void {
    window.location.href = `${API_BASE_URL}/auth/github`;
  },

  signInWithGoogle(): void {
    window.location.href = `${API_BASE_URL}/auth/google`;
  },

  async getMe(): Promise<User> {
    return request<User>("/auth/me");
  },

  signOut(): void {
    localStorage.removeItem("pruv_token");
    window.location.href = "/auth/signin";
  },

  setToken(token: string): void {
    localStorage.setItem("pruv_token", token);
  },

  getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("pruv_token");
  },
};

// ─── Dashboard ───────────────────────────────────────────────────────────────

export const dashboard = {
  async getStats(): Promise<DashboardStats> {
    return request<DashboardStats>("/dashboard/stats");
  },
};

// ─── Chains ──────────────────────────────────────────────────────────────────

export const chains = {
  async list(
    filters: ChainFilters = {}
  ): Promise<PaginatedResponse<Chain>> {
    const qs = buildQueryString(filters as Record<string, unknown>);
    return request<PaginatedResponse<Chain>>(`/chains${qs}`);
  },

  async get(id: string): Promise<Chain> {
    return request<Chain>(`/chains/${id}`);
  },

  async create(data: {
    name: string;
    description?: string;
    tags?: string[];
  }): Promise<Chain> {
    return request<Chain>("/chains", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async update(
    id: string,
    data: Partial<Pick<Chain, "name" | "description" | "tags">>
  ): Promise<Chain> {
    return request<Chain>(`/chains/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async delete(id: string): Promise<void> {
    return request<void>(`/chains/${id}`, { method: "DELETE" });
  },

  async verify(id: string): Promise<EntryValidation[]> {
    return request<EntryValidation[]>(`/chains/${id}/verify`);
  },
};

// ─── Entries ─────────────────────────────────────────────────────────────────

export const entries = {
  async list(
    chainId: string,
    params: { page?: number; per_page?: number } = {}
  ): Promise<PaginatedResponse<Entry>> {
    const qs = buildQueryString(params as Record<string, unknown>);
    return request<PaginatedResponse<Entry>>(
      `/chains/${chainId}/entries${qs}`
    );
  },

  async get(chainId: string, index: number): Promise<Entry> {
    return request<Entry>(`/chains/${chainId}/entries/${index}`);
  },

  async create(
    chainId: string,
    data: {
      y: string;
      action: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<Entry> {
    return request<Entry>(`/chains/${chainId}/entries`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async validate(
    chainId: string,
    index: number
  ): Promise<EntryValidation> {
    return request<EntryValidation>(
      `/chains/${chainId}/entries/${index}/validate`
    );
  },

  async undo(chainId: string): Promise<Entry> {
    return request<Entry>(`/chains/${chainId}/undo`, {
      method: "POST",
    });
  },
};

// ─── Receipts ────────────────────────────────────────────────────────────────

export const receipts = {
  async list(
    filters: ReceiptFilters = {}
  ): Promise<PaginatedResponse<Receipt>> {
    const qs = buildQueryString(filters as Record<string, unknown>);
    return request<PaginatedResponse<Receipt>>(`/receipts${qs}`);
  },

  async get(id: string): Promise<Receipt> {
    return request<Receipt>(`/receipts/${id}`);
  },

  async create(chainId: string): Promise<Receipt> {
    return request<Receipt>("/receipts", {
      method: "POST",
      body: JSON.stringify({ chain_id: chainId }),
    });
  },

  async getPdf(id: string): Promise<Blob> {
    const url = `${API_BASE_URL}/receipts/${id}/pdf`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Failed to fetch PDF");
    return res.blob();
  },

  async getBadgeUrl(id: string): Promise<string> {
    return `${API_BASE_URL}/receipts/${id}/badge`;
  },
};

// ─── Scans ───────────────────────────────────────────────────────────────────

export const scans = {
  async trigger(data: ScanRequest): Promise<ScanResult> {
    if (data.file) {
      const formData = new FormData();
      formData.append("file", data.file);
      if (data.chain_id) formData.append("chain_id", data.chain_id);
      if (data.options) {
        formData.append("options", JSON.stringify(data.options));
      }

      const url = `${API_BASE_URL}/scans`;
      const res = await fetch(url, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      });
      if (!res.ok) throw await res.json();
      return res.json();
    }

    return request<ScanResult>("/scans", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getStatus(id: string): Promise<ScanResult> {
    return request<ScanResult>(`/scans/${id}`);
  },
};

// ─── API Keys ────────────────────────────────────────────────────────────────

export const apiKeys = {
  async list(): Promise<ApiKey[]> {
    return request<ApiKey[]>("/settings/api-keys");
  },

  async create(data: {
    name: string;
    environment: "live" | "test";
    scopes: ApiKeyScope[];
    expires_in_days?: number;
  }): Promise<ApiKeyCreateResponse> {
    return request<ApiKeyCreateResponse>("/settings/api-keys", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async revoke(id: string): Promise<void> {
    return request<void>(`/settings/api-keys/${id}`, {
      method: "DELETE",
    });
  },
};

// ─── Team ────────────────────────────────────────────────────────────────────

export const team = {
  async listMembers(): Promise<TeamMember[]> {
    return request<TeamMember[]>("/settings/team/members");
  },

  async inviteMember(data: {
    email: string;
    role: TeamRole;
  }): Promise<TeamInvite> {
    return request<TeamInvite>("/settings/team/invites", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async removeMember(id: string): Promise<void> {
    return request<void>(`/settings/team/members/${id}`, {
      method: "DELETE",
    });
  },

  async updateRole(id: string, role: TeamRole): Promise<TeamMember> {
    return request<TeamMember>(`/settings/team/members/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
  },

  async listInvites(): Promise<TeamInvite[]> {
    return request<TeamInvite[]>("/settings/team/invites");
  },

  async cancelInvite(id: string): Promise<void> {
    return request<void>(`/settings/team/invites/${id}`, {
      method: "DELETE",
    });
  },
};

// ─── Billing ─────────────────────────────────────────────────────────────────

export const billing = {
  async getSubscription(): Promise<BillingSubscription> {
    return request<BillingSubscription>("/settings/billing/subscription");
  },

  async getUsage(): Promise<BillingUsage> {
    return request<BillingUsage>("/settings/billing/usage");
  },

  async getPlans(): Promise<BillingPlan[]> {
    return request<BillingPlan[]>("/settings/billing/plans");
  },

  async changePlan(planId: string): Promise<BillingSubscription> {
    return request<BillingSubscription>("/settings/billing/subscription", {
      method: "PUT",
      body: JSON.stringify({ plan_id: planId }),
    });
  },

  async getPortalUrl(): Promise<{ url: string }> {
    return request<{ url: string }>("/settings/billing/portal");
  },
};
