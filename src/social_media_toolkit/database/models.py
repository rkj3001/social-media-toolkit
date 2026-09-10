"""Persistent records used by downloader jobs and the future media library."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from social_media_toolkit.config import Category
from social_media_toolkit.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(StrEnum):
    QUEUED = "queued"
    DISCOVERING = "discovering"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaStatus(StrEnum):
    DISCOVERED = "discovered"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    DUPLICATE = "duplicate"
    FAILED = "failed"


class SourceAccount(Base):
    """A public profile entered by the user as a media source."""

    __tablename__ = "source_accounts"
    __table_args__ = (
        UniqueConstraint("platform", "username", name="uq_source_platform_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), default="instagram")
    username: Mapped[str] = mapped_column(String(64))
    profile_url: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    jobs: Mapped[list[DownloadJob]] = relationship(back_populates="account")
    posts: Mapped[list[SourcePost]] = relationship(back_populates="account")


class DownloadJob(Base):
    """A resumable request to discover and download media from one account."""

    __tablename__ = "download_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("source_accounts.id", ondelete="RESTRICT"), index=True
    )
    category: Mapped[Category] = mapped_column(
        Enum(Category, native_enum=False, values_callable=lambda enum: [e.value for e in enum])
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            native_enum=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=JobStatus.QUEUED,
        index=True,
    )
    discovered_count: Mapped[int] = mapped_column(Integer, default=0)
    queued_count: Mapped[int] = mapped_column(Integer, default=0)
    downloaded_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account: Mapped[SourceAccount] = relationship(back_populates="jobs")


class SourcePost(Base):
    """Instagram post metadata; captions remain attached to their source."""

    __tablename__ = "source_posts"
    __table_args__ = (
        UniqueConstraint(
            "platform", "platform_media_id", name="uq_source_post_platform_media"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("source_accounts.id", ondelete="RESTRICT"), index=True
    )
    platform: Mapped[str] = mapped_column(String(32), default="instagram")
    platform_media_id: Mapped[str] = mapped_column(String(128))
    shortcode: Mapped[str] = mapped_column(String(64), index=True)
    permalink: Mapped[str] = mapped_column(String(512))
    caption: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    media_type: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    account: Mapped[SourceAccount] = relationship(back_populates="posts")
    media_items: Mapped[list[SourceMediaItem]] = relationship(back_populates="post")


class CanonicalMedia(Base):
    """One physical video file, shared by every duplicate source item."""

    __tablename__ = "canonical_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    relative_path: Mapped[str] = mapped_column(String(1024), unique=True)
    byte_size: Mapped[int] = mapped_column(Integer)
    has_audio: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    sources: Mapped[list[SourceMediaItem]] = relationship(
        back_populates="canonical_media"
    )


class SourceMediaItem(Base):
    """One video within a post or carousel."""

    __tablename__ = "source_media_items"
    __table_args__ = (
        UniqueConstraint("source_post_id", "item_index", name="uq_post_media_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_post_id: Mapped[int] = mapped_column(
        ForeignKey("source_posts.id", ondelete="CASCADE"), index=True
    )
    item_index: Mapped[int] = mapped_column(Integer)
    platform_media_id: Mapped[str] = mapped_column(String(160), unique=True)
    status: Mapped[MediaStatus] = mapped_column(
        Enum(
            MediaStatus,
            native_enum=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=MediaStatus.DISCOVERED,
        index=True,
    )
    canonical_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_media.id", ondelete="RESTRICT"), index=True
    )
    last_error: Mapped[str | None] = mapped_column(Text)

    post: Mapped[SourcePost] = relationship(back_populates="media_items")
    canonical_media: Mapped[CanonicalMedia | None] = relationship(
        back_populates="sources"
    )
