"""Create source accounts and download jobs.

Revision ID: 20260910_01
Revises:
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("profile_url", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "platform", "username", name="uq_source_platform_username"
        ),
    )
    op.create_table(
        "download_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "dog",
                "cat",
                "entertainment",
                "uncategorized",
                name="category",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "discovering",
                "downloading",
                "completed",
                "failed",
                name="jobstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("discovered_count", sa.Integer(), nullable=False),
        sa.Column("queued_count", sa.Integer(), nullable=False),
        sa.Column("downloaded_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"], ["source_accounts.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_download_jobs_account_id", "download_jobs", ["account_id"]
    )
    op.create_index("ix_download_jobs_created_at", "download_jobs", ["created_at"])
    op.create_index("ix_download_jobs_status", "download_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_download_jobs_status", table_name="download_jobs")
    op.drop_index("ix_download_jobs_created_at", table_name="download_jobs")
    op.drop_index("ix_download_jobs_account_id", table_name="download_jobs")
    op.drop_table("download_jobs")
    op.drop_table("source_accounts")

