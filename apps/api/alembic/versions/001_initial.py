"""Initial migration — create all tables.

Revision ID: 001
Create Date: 2026-02-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("avatar_url", sa.Text),
        sa.Column("plan", sa.String(50), default="free", nullable=False),
        sa.Column("entries_this_month", sa.Integer, default=0),
        sa.Column("month_reset_at", sa.DateTime),
        sa.Column("github_id", sa.String(100), unique=True),
        sa.Column("google_id", sa.String(100), unique=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), default="Default"),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("scopes", postgresql.JSON, default=["read", "write"]),
        sa.Column("last_used_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"])

    # Chains
    op.create_table(
        "chains",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("length", sa.Integer, default=0),
        sa.Column("root_xy", sa.String(67)),
        sa.Column("head_xy", sa.String(67)),
        sa.Column("head_y", sa.String(64)),
        sa.Column("auto_redact", sa.Boolean, default=True),
        sa.Column("share_id", sa.String(36), unique=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_chains_user_id", "chains", ["user_id"])
    op.create_index("idx_chains_share_id", "chains", ["share_id"])

    # Entries
    op.create_table(
        "entries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("chain_id", sa.String(36), sa.ForeignKey("chains.id"), nullable=False),
        sa.Column("index", sa.Integer, nullable=False),
        sa.Column("timestamp", sa.Float, nullable=False),
        sa.Column("operation", sa.String(255), nullable=False),
        sa.Column("x", sa.String(64), nullable=False),
        sa.Column("y", sa.String(64), nullable=False),
        sa.Column("xy", sa.String(67), nullable=False),
        sa.Column("x_state", postgresql.JSON),
        sa.Column("y_state", postgresql.JSON),
        sa.Column("status", sa.String(20), default="success"),
        sa.Column("verified", sa.Boolean, default=True),
        sa.Column("metadata", postgresql.JSON, default={}),
        sa.Column("signature", sa.Text),
        sa.Column("signer_id", sa.String(255)),
        sa.Column("public_key", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_entries_chain_index", "entries", ["chain_id", "index"], unique=True)

    # Checkpoints
    op.create_table(
        "checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("chain_id", sa.String(36), sa.ForeignKey("chains.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("entry_index", sa.Integer, nullable=False),
        sa.Column("snapshot_data", postgresql.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_checkpoints_chain_id", "checkpoints", ["chain_id"])

    # Receipts
    op.create_table(
        "receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("chain_id", sa.String(36), sa.ForeignKey("chains.id"), nullable=False),
        sa.Column("task", sa.Text, nullable=False),
        sa.Column("started", sa.Float),
        sa.Column("completed", sa.Float),
        sa.Column("duration", sa.Float),
        sa.Column("entry_count", sa.Integer),
        sa.Column("first_x", sa.String(64)),
        sa.Column("final_y", sa.String(64)),
        sa.Column("root_xy", sa.String(67)),
        sa.Column("head_xy", sa.String(67)),
        sa.Column("all_verified", sa.Boolean, default=True),
        sa.Column("all_signatures_valid", sa.Boolean, default=True),
        sa.Column("receipt_hash", sa.String(64)),
        sa.Column("agent_type", sa.String(100)),
        sa.Column("metadata", postgresql.JSON, default={}),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_receipts_chain_id", "receipts", ["chain_id"])

    # Webhooks
    op.create_table(
        "webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("events", postgresql.JSON, default=["chain.created", "entry.appended"]),
        sa.Column("secret", sa.String(64)),
        sa.Column("active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("webhooks")
    op.drop_table("receipts")
    op.drop_table("checkpoints")
    op.drop_table("entries")
    op.drop_table("chains")
    op.drop_table("api_keys")
    op.drop_table("users")
