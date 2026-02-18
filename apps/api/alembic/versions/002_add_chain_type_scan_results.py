"""Add chain_type, description, tags to chains; user_id to receipts; scan_results table.

Revision ID: 002
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to chains
    op.add_column("chains", sa.Column("description", sa.Text, nullable=True))
    op.add_column("chains", sa.Column("tags", postgresql.JSON, server_default="[]"))
    op.add_column("chains", sa.Column("chain_type", sa.String(50), server_default="custom"))

    # Add user_id to receipts
    op.add_column("receipts", sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True))

    # Create scan_results table
    op.create_table(
        "scan_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(20), default="completed"),
        sa.Column("chain_id", sa.String(36), nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("findings", postgresql.JSON, default=[]),
        sa.Column("receipt_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_scan_results_user_id", "scan_results", ["user_id"])


def downgrade() -> None:
    op.drop_table("scan_results")
    op.drop_column("receipts", "user_id")
    op.drop_column("chains", "chain_type")
    op.drop_column("chains", "tags")
    op.drop_column("chains", "description")
