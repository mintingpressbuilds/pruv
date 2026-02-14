"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ──── Chain Schemas ────


class ChainCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    auto_redact: bool = True


class ChainUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)
    auto_redact: bool | None = None


class ChainResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    length: int
    root_xy: str | None = None
    head_xy: str | None = None
    head_y: str | None = None
    auto_redact: bool = True
    share_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChainListResponse(BaseModel):
    chains: list[ChainResponse]
    total: int


class ChainVerifyResponse(BaseModel):
    chain_id: str
    valid: bool
    length: int
    break_index: int | None = None


class ChainShareResponse(BaseModel):
    chain_id: str
    share_id: str
    share_url: str


# ──── Entry Schemas ────


VALID_ENTRY_STATUSES = {"success", "failed", "pending", "skipped"}


class EntryCreate(BaseModel):
    operation: str = Field(..., min_length=1, max_length=255)
    x_state: dict[str, Any] | None = None
    y_state: dict[str, Any] | None = None
    status: str = Field(default="success", pattern=r"^(success|failed|pending|skipped)$")
    metadata: dict[str, Any] = Field(default_factory=dict)
    signature: str | None = Field(default=None, max_length=200)
    signer_id: str | None = Field(default=None, max_length=255)
    public_key: str | None = Field(default=None, max_length=500)


class EntryBatchCreate(BaseModel):
    entries: list[EntryCreate] = Field(..., min_length=1, max_length=100)


class EntryResponse(BaseModel):
    id: str | None = None
    index: int
    timestamp: float
    operation: str
    x: str
    y: str
    xy: str
    x_state: dict[str, Any] | None = None
    y_state: dict[str, Any] | None = None
    status: str = "success"
    verified: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    signature: str | None = None
    signer_id: str | None = None
    public_key: str | None = None

    model_config = {"from_attributes": True}


class EntryListResponse(BaseModel):
    entries: list[EntryResponse]
    total: int


# ──── Checkpoint Schemas ────


class CheckpointCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class CheckpointResponse(BaseModel):
    id: str
    chain_id: str
    name: str
    entry_index: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CheckpointListResponse(BaseModel):
    checkpoints: list[CheckpointResponse]


class CheckpointPreviewResponse(BaseModel):
    checkpoint_id: str
    checkpoint_name: str
    current_entry_index: int
    target_entry_index: int
    entries_to_rollback: int


class CheckpointRestoreResponse(BaseModel):
    restored: bool
    checkpoint_id: str
    new_length: int


# ──── Entry Validation Schemas ────


class EntryValidationResponse(BaseModel):
    index: int
    valid: bool
    reason: str | None = None
    x_matches_prev_y: bool
    proof_valid: bool
    signature_valid: bool | None = None


# ──── Receipt Schemas ────


class ReceiptCreate(BaseModel):
    chain_id: str = Field(..., min_length=1, max_length=36)
    task: str = Field(default="verification", min_length=1, max_length=1000)
    agent_type: str | None = Field(default=None, max_length=100)


class ReceiptListResponse(BaseModel):
    receipts: list["ReceiptResponse"]
    total: int


class ReceiptResponse(BaseModel):
    id: str
    chain_id: str
    task: str
    started: float | None = None
    completed: float | None = None
    duration: float | None = None
    entry_count: int | None = None
    first_x: str | None = None
    final_y: str | None = None
    root_xy: str | None = None
    head_xy: str | None = None
    all_verified: bool = True
    all_signatures_valid: bool = True
    receipt_hash: str | None = None
    agent_type: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ──── Certificate Schemas ────


class CertificateResponse(BaseModel):
    chain_id: str
    chain_name: str
    valid: bool
    length: int
    root_xy: str | None = None
    head_xy: str | None = None
    verified_at: datetime
    break_index: int | None = None


# ──── Shared Chain Schemas ────


class SharedChainResponse(BaseModel):
    chain: ChainResponse
    entries: list[EntryResponse]
    verified: bool


# ──── Auth Schemas ────


VALID_SCOPES = {"read", "write", "admin"}


class ApiKeyCreate(BaseModel):
    name: str = Field(default="Default", min_length=1, max_length=255)
    scopes: list[str] = Field(default=["read", "write"], max_length=10)

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: list[str]) -> list[str]:
        invalid = set(v) - VALID_SCOPES
        if invalid:
            raise ValueError(f"Invalid scopes: {', '.join(sorted(invalid))}. Must be: {', '.join(sorted(VALID_SCOPES))}")
        return v


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: list[str] | Any = None
    created_at: datetime | None = None
    last_used_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key: str  # Full key, only shown once
    key_prefix: str
    scopes: list[str]


# ──── Error Schemas ────


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


# ──── Health ────


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


# ──── Dashboard Schemas ────


class ActivityItemResponse(BaseModel):
    id: str
    type: str
    description: str
    timestamp: float
    chain_id: str | None = None
    chain_name: str | None = None
    actor: str


class DashboardStatsResponse(BaseModel):
    total_chains: int
    total_entries: int
    total_receipts: int
    verified_percentage: float
    recent_activity: list[ActivityItemResponse]
