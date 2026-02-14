// ─── Core Domain Types ───────────────────────────────────────────────────────

export interface Chain {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  entry_count: number;
  status: ChainStatus;
  owner_id: string;
  tags: string[];
  metadata?: Record<string, unknown>;
}

export type ChainStatus = "valid" | "broken" | "pending" | "archived";

export interface Entry {
  index: number;
  chain_id: string;
  x: string;
  y: string;
  xy_proof: string; // format: xy_{sha256_hex}
  timestamp: string;
  actor: string;
  action: string;
  signed: boolean;
  signature?: string;
  metadata?: Record<string, unknown>;
}

export interface EntryValidation {
  index: number;
  valid: boolean;
  reason?: string;
  x_matches_prev_y: boolean;
  proof_valid: boolean;
  signature_valid?: boolean;
}

export interface Receipt {
  id: string;
  chain_id: string;
  chain_name: string;
  created_at: string;
  status: ReceiptStatus;
  entry_range: {
    start: number;
    end: number;
  };
  verification_result: VerificationResult;
  thinking_phase?: ThinkingPhase;
  issuer: string;
  badge_url?: string;
  pdf_url?: string;
}

export type ReceiptStatus = "verified" | "failed" | "pending" | "expired";

export interface VerificationResult {
  valid: boolean;
  checked_at: string;
  entries_checked: number;
  broken_links: number[];
  invalid_proofs: number[];
  unsigned_entries: number[];
  summary: string;
}

export interface ThinkingPhase {
  started_at: string;
  completed_at?: string;
  steps: ThinkingStep[];
}

export interface ThinkingStep {
  index: number;
  description: string;
  status: "completed" | "in_progress" | "pending" | "failed";
  duration_ms?: number;
}

// ─── API Key Types ───────────────────────────────────────────────────────────

export interface ApiKey {
  id: string;
  name: string;
  prefix: string; // pv_live_ or pv_test_
  created_at: string;
  last_used_at?: string;
  expires_at?: string;
  scopes: ApiKeyScope[];
  environment: "live" | "test";
}

export type ApiKeyScope =
  | "chains:read"
  | "chains:write"
  | "entries:read"
  | "entries:write"
  | "receipts:read"
  | "receipts:create"
  | "scan:trigger";

export interface ApiKeyCreateResponse {
  key: string; // full key, shown only once
  api_key: ApiKey;
}

// ─── Team Types ──────────────────────────────────────────────────────────────

export interface TeamMember {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: TeamRole;
  joined_at: string;
}

export type TeamRole = "owner" | "admin" | "member" | "viewer";

export interface TeamInvite {
  id: string;
  email: string;
  role: TeamRole;
  invited_at: string;
  expires_at: string;
  status: "pending" | "accepted" | "expired";
}

// ─── Billing Types ───────────────────────────────────────────────────────────

export interface BillingPlan {
  id: string;
  name: string;
  tier: "free" | "pro" | "team" | "enterprise";
  price_monthly: number;
  price_yearly: number;
  limits: {
    chains: number;
    entries_per_chain: number;
    receipts: number;
    team_members: number;
    api_keys: number;
  };
  features: string[];
}

export interface BillingSubscription {
  plan: BillingPlan;
  status: "active" | "past_due" | "cancelled" | "trialing";
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export interface BillingUsage {
  chains_used: number;
  chains_limit: number;
  entries_used: number;
  receipts_used: number;
  receipts_limit: number;
  api_keys_used: number;
  api_keys_limit: number;
  team_members_used: number;
  team_members_limit: number;
}

// ─── Scan Types ──────────────────────────────────────────────────────────────

export interface ScanRequest {
  chain_id?: string;
  source_url?: string;
  file?: File;
  options?: {
    deep_verify: boolean;
    check_signatures: boolean;
    generate_receipt: boolean;
  };
}

export interface ScanResult {
  id: string;
  status: "queued" | "scanning" | "completed" | "failed";
  chain_id?: string;
  started_at: string;
  completed_at?: string;
  findings: ScanFinding[];
  receipt_id?: string;
}

export interface ScanFinding {
  severity: "critical" | "warning" | "info";
  type: string;
  message: string;
  entry_index?: number;
  details?: Record<string, unknown>;
}

// ─── User Types ──────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  provider: "github" | "google";
  created_at: string;
}

// ─── API Response Types ──────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface ApiError {
  error: string;
  message: string;
  status: number;
  details?: Record<string, unknown>;
}

// ─── Dashboard Stats ─────────────────────────────────────────────────────────

export interface DashboardStats {
  total_chains: number;
  total_entries: number;
  total_receipts: number;
  verified_percentage: number;
  recent_activity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: "chain_created" | "entry_added" | "receipt_issued" | "scan_completed" | "chain_broken";
  description: string;
  timestamp: string;
  chain_id?: string;
  chain_name?: string;
  actor: string;
}

// ─── Checkpoint Types ────────────────────────────────────────────────────────

export interface Checkpoint {
  id: string;
  chain_id: string;
  name: string;
  entry_index: number;
  created_at: string;
}

export interface CheckpointPreview {
  checkpoint_id: string;
  checkpoint_name: string;
  current_entry_index: number;
  target_entry_index: number;
  entries_to_rollback: number;
}

export interface CheckpointRestoreResult {
  restored: boolean;
  checkpoint_id: string;
  new_length: number;
}

// ─── Filter / Sort Types ─────────────────────────────────────────────────────

export interface ChainFilters {
  status?: ChainStatus;
  search?: string;
  tags?: string[];
  sort_by?: "created_at" | "updated_at" | "name" | "entry_count";
  sort_order?: "asc" | "desc";
  page?: number;
  per_page?: number;
}

export interface ReceiptFilters {
  status?: ReceiptStatus;
  chain_id?: string;
  search?: string;
  sort_by?: "created_at" | "status";
  sort_order?: "asc" | "desc";
  page?: number;
  per_page?: number;
}
