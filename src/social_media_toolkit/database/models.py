"""Persistent records used by downloader jobs and the future media library."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
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

