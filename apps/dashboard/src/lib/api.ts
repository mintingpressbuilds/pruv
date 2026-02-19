import type {
  AgentIdentity,
  AgentType,
  Chain,
  Entry,
  EntryValidation,
  IdentityVerification,
  ProvenanceArtifact,
  ProvenanceVerification,
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
  Checkpoint,
  CheckpointPreview,
  CheckpointRestoreResult,
  ChainAlerts,
  PaymentVerification,
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

// ─── Response Transformers ──────────────────────────────────────────────────

// Backend chain → Frontend Chain
interface BackendChain {
  id: string;
  name: string;
  description?: string;
  tags?: string[];
  chain_type?: string;
  length: number;
  root_xy: string | null;
  head_xy: string | null;
  head_y: string | null;
  auto_redact: boolean;
  share_id: string | null;
  created_at: number | string | null;
  updated_at: number | string | null;
  user_id?: string;
  metadata?: Record<string, unknown>;
}

function transformChain(raw: BackendChain): Chain {
  return {
    id: raw.id,
    name: raw.name,
    description: raw.description,
    chain_type: (raw.chain_type as Chain["chain_type"]) ?? "custom",
    created_at: typeof raw.created_at === "number"
      ? new Date(raw.created_at * 1000).toISOString()
      : raw.created_at ?? new Date().toISOString(),
    updated_at: typeof raw.updated_at === "number"
      ? new Date(raw.updated_at * 1000).toISOString()
      : raw.updated_at ?? new Date().toISOString(),
    entry_count: raw.length,
    status: "valid",
    owner_id: raw.user_id ?? "",
    tags: raw.tags ?? [],
    metadata: raw.metadata ?? {},
  };
}

// Backend entry → Frontend Entry
interface BackendEntry {
  id?: string;
  chain_id?: string;
  index: number;
  timestamp: number;
  operation: string;
  x: string;
  y: string;
  xy: string;
  x_state?: Record<string, unknown> | null;
  y_state?: Record<string, unknown> | null;
  status: string;
  verified: boolean;
  metadata: Record<string, unknown>;
  signature?: string | null;
  signer_id?: string | null;
  public_key?: string | null;
}

function transformEntry(raw: BackendEntry): Entry {
  return {
    index: raw.index,
    chain_id: raw.chain_id ?? "",
    x: raw.x,
    y: raw.y,
    xy_proof: raw.xy,
    timestamp: typeof raw.timestamp === "number"
      ? new Date(raw.timestamp * 1000).toISOString()
      : String(raw.timestamp),
    actor: raw.signer_id ?? "system",
    action: raw.operation,
    signed: !!raw.signature,
    signature: raw.signature ?? undefined,
    metadata: raw.metadata,
  };
}

// Backend receipt → Frontend Receipt
interface BackendReceipt {
  id: string;
  chain_id: string;
  task: string;
  started?: number | null;
  completed?: number | null;
  duration?: number | null;
  entry_count?: number | null;
  first_x?: string | null;
  final_y?: string | null;
  root_xy?: string | null;
  head_xy?: string | null;
  all_verified: boolean;
  all_signatures_valid: boolean;
  receipt_hash?: string | null;
  agent_type?: string | null;
  created_at?: number | string | null;
}

function transformReceipt(raw: BackendReceipt): Receipt {
  return {
    id: raw.id,
    chain_id: raw.chain_id,
    chain_name: raw.task,
    created_at: typeof raw.created_at === "number"
      ? new Date(raw.created_at * 1000).toISOString()
      : raw.created_at ?? new Date().toISOString(),
    status: raw.all_verified ? "verified" : "failed",
    entry_range: {
      start: 0,
      end: (raw.entry_count ?? 1) - 1,
    },
    verification_result: {
      valid: raw.all_verified,
      checked_at: typeof raw.completed === "number"
        ? new Date(raw.completed * 1000).toISOString()
        : new Date().toISOString(),
      entries_checked: raw.entry_count ?? 0,
      broken_links: [],
      invalid_proofs: [],
      unsigned_entries: [],
      summary: raw.all_verified ? "all entries verified" : "verification failed",
    },
    issuer: raw.agent_type ?? "pruv",
    badge_url: `${API_BASE_URL}/v1/receipts/${raw.id}/badge`,
    pdf_url: `${API_BASE_URL}/v1/receipts/${raw.id}/pdf`,
  };
}

// Backend verify response → Frontend EntryValidation[]
interface BackendVerifyResponse {
  chain_id: string;
  valid: boolean;
  length: number;
  break_index: number | null;
}

function transformVerification(raw: BackendVerifyResponse): EntryValidation[] {
  const validations: EntryValidation[] = [];
  for (let i = 0; i < raw.length; i++) {
    const isBroken = raw.break_index !== null && i === raw.break_index;
    validations.push({
      index: i,
      valid: !isBroken,
      reason: isBroken ? "chain link broken at this entry" : undefined,
      x_matches_prev_y: !isBroken,
      proof_valid: !isBroken,
    });
  }
  return validations;
}

// Backend API key → Frontend ApiKey
interface BackendApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  created_at?: number | string | null;
  last_used_at?: number | string | null;
}

function transformApiKey(raw: BackendApiKey): ApiKey {
  const prefix = raw.key_prefix.replace("…", "").replace("...", "");
  return {
    id: raw.id,
    name: raw.name,
    prefix: raw.key_prefix,
    created_at: typeof raw.created_at === "number"
      ? new Date(raw.created_at * 1000).toISOString()
      : raw.created_at ?? new Date().toISOString(),
    last_used_at: raw.last_used_at
      ? typeof raw.last_used_at === "number"
        ? new Date(raw.last_used_at * 1000).toISOString()
        : raw.last_used_at
      : undefined,
    scopes: raw.scopes as ApiKeyScope[],
    environment: prefix.includes("pv_test_") ? "test" : "live",
  };
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export const auth = {
  signInWithGitHub(): void {
    window.location.href = `${API_BASE_URL}/v1/auth/oauth/github`;
  },

  async getMe(): Promise<User> {
    return request<User>("/v1/auth/me");
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
    const raw = await request<{
      total_chains: number;
      total_entries: number;
      total_receipts: number;
      verified_percentage: number;
      recent_activity: Array<{
        id: string;
        type: string;
        description: string;
        timestamp: number;
        chain_id?: string;
        chain_name?: string;
        actor: string;
      }>;
    }>("/v1/dashboard/stats");

    return {
      total_chains: raw.total_chains,
      total_entries: raw.total_entries,
      total_receipts: raw.total_receipts,
      verified_percentage: raw.verified_percentage,
      recent_activity: raw.recent_activity.map((a) => ({
        ...a,
        type: a.type as DashboardStats["recent_activity"][0]["type"],
        timestamp: typeof a.timestamp === "number"
          ? new Date(a.timestamp * 1000).toISOString()
          : String(a.timestamp),
      })),
    };
  },
};

// ─── Chains ──────────────────────────────────────────────────────────────────

export const chains = {
  async list(
    filters: ChainFilters = {}
  ): Promise<PaginatedResponse<Chain>> {
    const qs = buildQueryString(filters as Record<string, unknown>);
    const raw = await request<{ chains: BackendChain[]; total: number }>(
      `/v1/chains${qs}`
    );
    const page = filters.page ?? 1;
    const per_page = filters.per_page ?? 100;
    return {
      data: raw.chains.map(transformChain),
      total: raw.total,
      page,
      per_page,
      has_more: page * per_page < raw.total,
    };
  },

  async get(id: string): Promise<Chain> {
    const raw = await request<BackendChain>(`/v1/chains/${id}`);
    return transformChain(raw);
  },

  async create(data: {
    name: string;
    description?: string;
    tags?: string[];
    chain_type?: string;
  }): Promise<Chain> {
    const raw = await request<BackendChain>("/v1/chains", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return transformChain(raw);
  },

  async update(
    id: string,
    data: Partial<Pick<Chain, "name" | "description" | "tags">>
  ): Promise<Chain> {
    const raw = await request<BackendChain>(`/v1/chains/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    return transformChain(raw);
  },

  async delete(id: string): Promise<void> {
    return request<void>(`/v1/chains/${id}`, { method: "DELETE" });
  },

  async verify(id: string): Promise<EntryValidation[]> {
    const raw = await request<BackendVerifyResponse>(`/v1/chains/${id}/verify`);
    return transformVerification(raw);
  },

  async share(id: string): Promise<{ share_id: string; share_url: string }> {
    return request<{ chain_id: string; share_id: string; share_url: string }>(
      `/v1/chains/${id}/share`
    );
  },

  async alerts(id: string): Promise<ChainAlerts> {
    return request<ChainAlerts>(`/v1/chains/${id}/alerts`);
  },

  async verifyPayments(id: string): Promise<PaymentVerification> {
    return request<PaymentVerification>(`/v1/chains/${id}/verify-payments`);
  },

  async exportHtml(id: string): Promise<string> {
    const url = `${API_BASE_URL}/v1/chains/${id}/export`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Failed to export chain");
    return res.text();
  },
};

// ─── Entries ─────────────────────────────────────────────────────────────────

export const entries = {
  async list(
    chainId: string,
    params: { page?: number; per_page?: number } = {}
  ): Promise<PaginatedResponse<Entry>> {
    const offset = ((params.page ?? 1) - 1) * (params.per_page ?? 100);
    const limit = params.per_page ?? 100;
    const qs = buildQueryString({ offset, limit });
    const raw = await request<{ entries: BackendEntry[]; total: number }>(
      `/v1/chains/${chainId}/entries${qs}`
    );
    const page = params.page ?? 1;
    const per_page = params.per_page ?? 100;
    return {
      data: raw.entries.map(transformEntry),
      total: raw.total,
      page,
      per_page,
      has_more: page * per_page < raw.total,
    };
  },

  async get(chainId: string, index: number): Promise<Entry> {
    const raw = await request<BackendEntry>(
      `/v1/chains/${chainId}/entries/${index}`
    );
    return transformEntry(raw);
  },

  async create(
    chainId: string,
    data: {
      y_state?: Record<string, unknown>;
      operation: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<Entry> {
    const raw = await request<BackendEntry>(`/v1/chains/${chainId}/entries`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    return transformEntry(raw);
  },

  async validate(
    chainId: string,
    index: number
  ): Promise<EntryValidation> {
    return request<EntryValidation>(
      `/v1/chains/${chainId}/entries/${index}/validate`
    );
  },

  async undo(chainId: string): Promise<Entry> {
    const raw = await request<BackendEntry>(`/v1/chains/${chainId}/undo`, {
      method: "POST",
    });
    return transformEntry(raw);
  },
};

// ─── Receipts ────────────────────────────────────────────────────────────────

export const receipts = {
  async list(
    filters: ReceiptFilters = {}
  ): Promise<PaginatedResponse<Receipt>> {
    const qs = buildQueryString(filters as Record<string, unknown>);
    const raw = await request<{ receipts: BackendReceipt[]; total: number }>(
      `/v1/receipts${qs}`
    );
    const page = filters.page ?? 1;
    const per_page = filters.per_page ?? 100;
    return {
      data: raw.receipts.map(transformReceipt),
      total: raw.total,
      page,
      per_page,
      has_more: page * per_page < raw.total,
    };
  },

  async get(id: string): Promise<Receipt> {
    const raw = await request<BackendReceipt>(`/v1/receipts/${id}`);
    return transformReceipt(raw);
  },

  async create(chainId: string): Promise<Receipt> {
    const raw = await request<BackendReceipt>("/v1/receipts", {
      method: "POST",
      body: JSON.stringify({ chain_id: chainId }),
    });
    return transformReceipt(raw);
  },

  async getPdf(id: string): Promise<Blob> {
    const url = `${API_BASE_URL}/v1/receipts/${id}/pdf`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Failed to fetch PDF");
    return res.blob();
  },

  async getBadgeUrl(id: string): Promise<string> {
    return `${API_BASE_URL}/v1/receipts/${id}/badge`;
  },
};

// ─── Checkpoints ─────────────────────────────────────────────────────────────

export const checkpoints = {
  async list(chainId: string): Promise<Checkpoint[]> {
    const raw = await request<{
      checkpoints: Array<{
        id: string;
        chain_id: string;
        name: string;
        entry_index: number;
        created_at: number | string | null;
      }>;
    }>(`/v1/chains/${chainId}/checkpoints`);
    return raw.checkpoints.map((cp) => ({
      id: cp.id,
      chain_id: cp.chain_id,
      name: cp.name,
      entry_index: cp.entry_index,
      created_at: typeof cp.created_at === "number"
        ? new Date(cp.created_at * 1000).toISOString()
        : cp.created_at ?? new Date().toISOString(),
    }));
  },

  async create(
    chainId: string,
    name: string
  ): Promise<Checkpoint> {
    const raw = await request<{
      id: string;
      chain_id: string;
      name: string;
      entry_index: number;
      created_at: number | string | null;
    }>(`/v1/chains/${chainId}/checkpoints`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    return {
      id: raw.id,
      chain_id: raw.chain_id,
      name: raw.name,
      entry_index: raw.entry_index,
      created_at: typeof raw.created_at === "number"
        ? new Date(raw.created_at * 1000).toISOString()
        : raw.created_at ?? new Date().toISOString(),
    };
  },

  async preview(
    chainId: string,
    checkpointId: string
  ): Promise<CheckpointPreview> {
    return request<CheckpointPreview>(
      `/v1/chains/${chainId}/checkpoints/${checkpointId}/preview`
    );
  },

  async restore(
    chainId: string,
    checkpointId: string
  ): Promise<CheckpointRestoreResult> {
    return request<CheckpointRestoreResult>(
      `/v1/chains/${chainId}/checkpoints/${checkpointId}/restore`,
      { method: "POST" }
    );
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

      const url = `${API_BASE_URL}/v1/scans`;
      const res = await fetch(url, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      });
      if (!res.ok) throw await res.json();
      return res.json();
    }

    return request<ScanResult>("/v1/scans", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async uploadZip(file: File): Promise<ScanResult> {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${API_BASE_URL}/v1/scans/upload`;
    const res = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw err;
    }
    return res.json();
  },

  async scanGitHub(repoUrl: string, branch?: string): Promise<ScanResult> {
    return request<ScanResult>("/v1/scans/github", {
      method: "POST",
      body: JSON.stringify({ url: repoUrl, branch: branch || "main" }),
    });
  },

  async scanUrl(url: string): Promise<ScanResult> {
    return request<ScanResult>("/v1/scans/url", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  },

  async getStatus(id: string): Promise<ScanResult> {
    return request<ScanResult>(`/v1/scans/${id}`);
  },

  async exportReceipt(scanId: string): Promise<void> {
    const url = `${API_BASE_URL}/v1/scans/${scanId}/receipt`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to export receipt");
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `pruv-receipt-${scanId}.html`;
    a.click();
    URL.revokeObjectURL(blobUrl);
  },
};

// ─── API Keys ────────────────────────────────────────────────────────────────

export const apiKeys = {
  async list(): Promise<ApiKey[]> {
    const raw = await request<{ keys: BackendApiKey[] }>("/v1/auth/api-keys");
    return raw.keys.map(transformApiKey);
  },

  async create(data: {
    name: string;
    environment: "live" | "test";
    scopes: ApiKeyScope[];
    expires_in_days?: number;
  }): Promise<ApiKeyCreateResponse> {
    const prefix = data.environment === "test" ? "pv_test_" : "pv_live_";
    const raw = await request<{
      id: string;
      name: string;
      key: string;
      key_prefix: string;
      scopes: string[];
    }>("/v1/auth/api-keys", {
      method: "POST",
      body: JSON.stringify({
        name: data.name,
        scopes: data.scopes,
        prefix,
      }),
    });
    return {
      key: raw.key,
      api_key: transformApiKey({
        id: raw.id,
        name: raw.name,
        key_prefix: raw.key_prefix,
        scopes: raw.scopes,
        created_at: Date.now() / 1000,
      }),
    };
  },

  async revoke(id: string): Promise<void> {
    return request<void>(`/v1/auth/api-keys/${id}`, {
      method: "DELETE",
    });
  },
};

// ─── Team ────────────────────────────────────────────────────────────────────

export const team = {
  async listMembers(): Promise<TeamMember[]> {
    return request<TeamMember[]>("/v1/settings/team/members");
  },

  async inviteMember(data: {
    email: string;
    role: TeamRole;
  }): Promise<TeamInvite> {
    return request<TeamInvite>("/v1/settings/team/invites", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async removeMember(id: string): Promise<void> {
    return request<void>(`/v1/settings/team/members/${id}`, {
      method: "DELETE",
    });
  },

  async updateRole(id: string, role: TeamRole): Promise<TeamMember> {
    return request<TeamMember>(`/v1/settings/team/members/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
  },

  async listInvites(): Promise<TeamInvite[]> {
    return request<TeamInvite[]>("/v1/settings/team/invites");
  },

  async cancelInvite(id: string): Promise<void> {
    return request<void>(`/v1/settings/team/invites/${id}`, {
      method: "DELETE",
    });
  },
};

// ─── Billing ─────────────────────────────────────────────────────────────────

export const billing = {
  async getSubscription(): Promise<BillingSubscription> {
    return request<BillingSubscription>("/v1/settings/billing/subscription");
  },

  async getUsage(): Promise<BillingUsage> {
    return request<BillingUsage>("/v1/settings/billing/usage");
  },

  async getPlans(): Promise<BillingPlan[]> {
    return request<BillingPlan[]>("/v1/settings/billing/plans");
  },

  async changePlan(planId: string): Promise<BillingSubscription> {
    return request<BillingSubscription>("/v1/settings/billing/subscription", {
      method: "PUT",
      body: JSON.stringify({ plan_id: planId }),
    });
  },

  async getPortalUrl(): Promise<{ url: string }> {
    return request<{ url: string }>("/v1/settings/billing/portal");
  },
};

// ─── Identity ───────────────────────────────────────────────────────────────

interface BackendIdentity {
  id: string;
  name: string;
  agent_type: string;
  public_key: string;
  chain_id: string;
  registered_at: number | string | null;
  action_count: number;
  last_action_at?: number | string | null;
  metadata?: Record<string, unknown>;
}

function transformIdentity(raw: BackendIdentity): AgentIdentity {
  return {
    id: raw.id,
    name: raw.name,
    agent_type: (raw.agent_type as AgentType) ?? "custom",
    public_key: raw.public_key,
    chain_id: raw.chain_id,
    registered_at:
      typeof raw.registered_at === "number"
        ? new Date(raw.registered_at * 1000).toISOString()
        : raw.registered_at ?? new Date().toISOString(),
    action_count: raw.action_count ?? 0,
    last_action_at: raw.last_action_at
      ? typeof raw.last_action_at === "number"
        ? new Date(raw.last_action_at * 1000).toISOString()
        : raw.last_action_at
      : undefined,
    metadata: raw.metadata ?? {},
  };
}

export const identities = {
  async list(): Promise<{ data: AgentIdentity[]; total: number }> {
    const raw = await request<{
      identities: BackendIdentity[];
      total: number;
    }>("/v1/identity");
    return {
      data: raw.identities.map(transformIdentity),
      total: raw.total,
    };
  },

  async get(id: string): Promise<AgentIdentity> {
    const raw = await request<BackendIdentity>(`/v1/identity/${id}`);
    return transformIdentity(raw);
  },

  async register(data: {
    name: string;
    agent_type?: string;
    metadata?: Record<string, unknown>;
  }): Promise<AgentIdentity> {
    const raw = await request<BackendIdentity>("/v1/identity/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return transformIdentity(raw);
  },

  async act(
    id: string,
    data: { action: string; data?: Record<string, unknown> }
  ): Promise<unknown> {
    return request(`/v1/identity/${id}/act`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async verify(id: string): Promise<IdentityVerification> {
    return request<IdentityVerification>(`/v1/identity/${id}/verify`);
  },

  async history(
    id: string,
    params?: { limit?: number; offset?: number }
  ): Promise<{ actions: unknown[]; total: number }> {
    const qs = buildQueryString((params ?? {}) as Record<string, unknown>);
    return request(`/v1/identity/${id}/history${qs}`);
  },

  getReceiptUrl(id: string): string {
    return `${API_BASE_URL}/v1/identity/${id}/receipt`;
  },
};

// ─── Provenance ─────────────────────────────────────────────────────────────

interface BackendArtifact {
  id: string;
  name: string;
  content_hash: string;
  content_type: string;
  creator: string;
  chain_id: string;
  created_at: number | string | null;
  current_hash: string;
  transition_count: number;
  last_modified_at?: number | string | null;
  metadata?: Record<string, unknown>;
}

function transformArtifact(raw: BackendArtifact): ProvenanceArtifact {
  return {
    id: raw.id,
    name: raw.name,
    content_hash: raw.content_hash,
    content_type: raw.content_type ?? "application/octet-stream",
    creator: raw.creator,
    chain_id: raw.chain_id,
    created_at:
      typeof raw.created_at === "number"
        ? new Date(raw.created_at * 1000).toISOString()
        : raw.created_at ?? new Date().toISOString(),
    current_hash: raw.current_hash,
    transition_count: raw.transition_count ?? 0,
    last_modified_at: raw.last_modified_at
      ? typeof raw.last_modified_at === "number"
        ? new Date(raw.last_modified_at * 1000).toISOString()
        : raw.last_modified_at
      : undefined,
    metadata: raw.metadata ?? {},
  };
}

export const provenanceApi = {
  async list(): Promise<{ data: ProvenanceArtifact[]; total: number }> {
    const raw = await request<{
      artifacts: BackendArtifact[];
      total: number;
    }>("/v1/provenance");
    return {
      data: raw.artifacts.map(transformArtifact),
      total: raw.total,
    };
  },

  async get(id: string): Promise<ProvenanceArtifact> {
    const raw = await request<BackendArtifact>(`/v1/provenance/${id}`);
    return transformArtifact(raw);
  },

  async origin(data: {
    content_hash: string;
    name: string;
    creator: string;
    content_type?: string;
    metadata?: Record<string, unknown>;
  }): Promise<ProvenanceArtifact> {
    const raw = await request<BackendArtifact>("/v1/provenance/origin", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return transformArtifact(raw);
  },

  async transition(
    id: string,
    data: {
      new_hash: string;
      modifier: string;
      reason?: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<unknown> {
    return request(`/v1/provenance/${id}/transition`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async verify(id: string): Promise<ProvenanceVerification> {
    return request<ProvenanceVerification>(`/v1/provenance/${id}/verify`);
  },

  async history(
    id: string,
    params?: { limit?: number; offset?: number }
  ): Promise<{ entries: unknown[]; total: number }> {
    const qs = buildQueryString((params ?? {}) as Record<string, unknown>);
    return request(`/v1/provenance/${id}/history${qs}`);
  },

  getReceiptUrl(id: string): string {
    return `${API_BASE_URL}/v1/provenance/${id}/receipt`;
  },
};
