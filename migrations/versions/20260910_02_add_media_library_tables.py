"""Add source post, source media, and canonical media tables.

Revision ID: 20260910_02
Revises: 20260910_01
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_02"
down_revision: str | None = "20260910_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("platform_media_id", sa.String(length=128), nullable=False),
        sa.Column("shortcode", sa.String(length=64), nullable=False),
        sa.Column("permalink", sa.String(length=512), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["source_accounts.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "platform", "platform_media_id", name="uq_source_post_platform_media"
        ),
    )
    op.create_index("ix_source_posts_account_id", "source_posts", ["account_id"])
    op.create_index("ix_source_posts_shortcode", "source_posts", ["shortcode"])
    op.create_index(
        "ix_source_posts_published_at", "source_posts", ["published_at"]
    )

    op.create_table(
        "canonical_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("relative_path", sa.String(length=1024), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("has_audio", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("relative_path"),
    )
    op.create_index(
        "ix_canonical_media_sha256", "canonical_media", ["sha256"], unique=True
    )

    op.create_table(
        "source_media_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_post_id", sa.Integer(), nullable=False),
        sa.Column("item_index", sa.Integer(), nullable=False),
        sa.Column("platform_media_id", sa.String(length=160), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "discovered",
                "downloading",
                "downloaded",
                "duplicate",
                "failed",
                name="mediastatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("canonical_media_id", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["canonical_media_id"], ["canonical_media.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_post_id"], ["source_posts.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "source_post_id", "item_index", name="uq_post_media_index"
        ),
        sa.UniqueConstraint("platform_media_id"),
    )
    op.create_index(
        "ix_source_media_items_source_post_id",
        "source_media_items",
        ["source_post_id"],
    )
    op.create_index(
        "ix_source_media_items_canonical_media_id",
        "source_media_items",
        ["canonical_media_id"],
    )
    op.create_index(
        "ix_source_media_items_status", "source_media_items", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_source_media_items_status", table_name="source_media_items")
    op.drop_index(
        "ix_source_media_items_canonical_media_id",
        table_name="source_media_items",
    )
    op.drop_index(
        "ix_source_media_items_source_post_id", table_name="source_media_items"
    )
    op.drop_table("source_media_items")
    op.drop_index("ix_canonical_media_sha256", table_name="canonical_media")
    op.drop_table("canonical_media")
    op.drop_index("ix_source_posts_published_at", table_name="source_posts")
    op.drop_index("ix_source_posts_shortcode", table_name="source_posts")
    op.drop_index("ix_source_posts_account_id", table_name="source_posts")
    op.drop_table("source_posts")
