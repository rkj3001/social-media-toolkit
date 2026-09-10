"""Synchronous downloader worker shared by the CLI and web background task."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator
from pathlib import Path

from instaloader.exceptions import InstaloaderException
from requests import RequestException
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from social_media_toolkit.config import Settings
from social_media_toolkit.database.models import (
    CanonicalMedia,
    DownloadJob,
    JobStatus,
    MediaStatus,
    SourceAccount,
    SourceMediaItem,
    SourcePost,
    utc_now,
)
from social_media_toolkit.database.session import (
    create_database_engine,
    create_session_factory,
)
from social_media_toolkit.integrations.instagram import (
    InstagramClient,
    InstagramVideo,
    InstaloaderClient,
)
from social_media_toolkit.storage import LibraryStorage


EXPECTED_DOWNLOAD_ERRORS = (
    InstaloaderException,
    RequestException,
    OSError,
    ValueError,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DownloadWorker:
    """Process one SQLite job at a time and keep every transition durable."""

    def __init__(
        self,
        settings: Settings,
        client: InstagramClient | None = None,
    ) -> None:
        self.settings = settings
        self.storage = LibraryStorage(settings.media_library_root)
        self.storage.initialize()
        self.engine: Engine = create_database_engine(settings)
        self.factory: sessionmaker[Session] = create_session_factory(self.engine)
        self.client = client or InstaloaderClient()

    def close(self) -> None:
        self.engine.dispose()

    def run(self, job_id: int) -> None:
        account = self._claim(job_id)
        if account is None:
            return

        try:
            videos = self.client.discover_videos(account.username)
            for video in videos:
                self._process_video(job_id, account, video)
        except EXPECTED_DOWNLOAD_ERRORS as error:
            self._fail_job(job_id, error)
            return

        with self.factory.begin() as session:
            job = session.get(DownloadJob, job_id)
            if job is not None:
                job.status = JobStatus.COMPLETED
                job.completed_at = utc_now()
            stored_account = session.get(SourceAccount, account.id)
            if stored_account is not None:
                stored_account.last_sync_at = utc_now()

    def _claim(self, job_id: int) -> SourceAccount | None:
        with self.factory.begin() as session:
            job = session.get(DownloadJob, job_id)
            if job is None:
                raise ValueError(f"Download job {job_id} does not exist")
            if job.status not in {JobStatus.QUEUED, JobStatus.FAILED}:
                return None

            job.status = JobStatus.DISCOVERING
            job.discovered_count = 0
            job.queued_count = 0
            job.downloaded_count = 0
            job.duplicate_count = 0
            job.failed_count = 0
            job.last_error = None
            job.completed_at = None
            return job.account

    def _process_video(
        self,
        job_id: int,
        account: SourceAccount,
        video: InstagramVideo,
    ) -> None:
        media_item_id, already_downloaded = self._reserve(
            job_id, account.id, video
        )
        if already_downloaded:
            return

        temporary = self.storage.prepare_file(
            Path("temporary") / f"job-{job_id}-{media_item_id}.partial"
        )
        try:
            self.client.download_video(video, temporary)
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise ValueError("Instagram returned an empty video file")
            self._store_download(
                job_id,
                media_item_id,
                account.username,
                video,
                temporary,
            )
        except EXPECTED_DOWNLOAD_ERRORS as error:
            temporary.unlink(missing_ok=True)
            with self.factory.begin() as session:
                media_item = session.get(SourceMediaItem, media_item_id)
                job = session.get(DownloadJob, job_id)
                if media_item is not None:
                    media_item.status = MediaStatus.FAILED
                    media_item.last_error = str(error)
                if job is not None:
                    job.queued_count -= 1
                    job.failed_count += 1
                    job.last_error = str(error)

    def _reserve(
        self,
        job_id: int,
        account_id: int,
        video: InstagramVideo,
    ) -> tuple[int, bool]:
        with self.factory.begin() as session:
            job = session.get(DownloadJob, job_id)
            if job is None:
                raise ValueError(f"Download job {job_id} disappeared")
            job.status = JobStatus.DOWNLOADING
            job.discovered_count += 1

            post = session.scalar(
                select(SourcePost).where(
                    SourcePost.platform == "instagram",
                    SourcePost.platform_media_id
                    == video.platform_media_id.split(":", 1)[0],
                )
            )
            if post is None:
                post = SourcePost(
                    account_id=account_id,
                    platform="instagram",
                    platform_media_id=video.platform_media_id.split(":", 1)[0],
                    shortcode=video.shortcode,
                    permalink=video.permalink,
                    caption=video.caption,
                    published_at=video.published_at,
                    media_type=video.media_type,
                )
                session.add(post)
                session.flush()

            media_item = session.scalar(
                select(SourceMediaItem).where(
                    SourceMediaItem.platform_media_id == video.platform_media_id
                )
            )
            if media_item is None:
                media_item = SourceMediaItem(
                    source_post_id=post.id,
                    item_index=video.item_index,
                    platform_media_id=video.platform_media_id,
                )
                session.add(media_item)
                session.flush()

            if media_item.canonical_media_id is not None:
                job.duplicate_count += 1
                return media_item.id, True

            media_item.status = MediaStatus.DOWNLOADING
            media_item.last_error = None
            job.queued_count += 1
            return media_item.id, False

    def _store_download(
        self,
        job_id: int,
        media_item_id: int,
        username: str,
        video: InstagramVideo,
        temporary: Path,
    ) -> None:
        digest = sha256_file(temporary)
        with self.factory.begin() as session:
            existing = session.scalar(
                select(CanonicalMedia).where(CanonicalMedia.sha256 == digest)
            )
            media_item = session.get(SourceMediaItem, media_item_id)
            job = session.get(DownloadJob, job_id)
            if media_item is None or job is None:
                raise ValueError("Reserved download record disappeared")

            if existing is not None:
                temporary.unlink(missing_ok=True)
                media_item.canonical_media_id = existing.id
                media_item.status = MediaStatus.DUPLICATE
                job.queued_count -= 1
                job.duplicate_count += 1
                return

            suffix = "" if video.item_index == 0 else f"-{video.item_index + 1}"
            relative_path = (
                Path("media")
                / job.category.value
                / username
                / f"{video.published_at:%Y}"
                / f"{video.published_at:%m}"
                / f"{video.shortcode}{suffix}.mp4"
            )
            destination = self.storage.prepare_file(relative_path)
            os.replace(temporary, destination)
            canonical = CanonicalMedia(
                sha256=digest,
                relative_path=relative_path.as_posix(),
                byte_size=destination.stat().st_size,
                # ffprobe will populate this once media validation is enabled.
                has_audio=None,
            )
            session.add(canonical)
            session.flush()
            media_item.canonical_media_id = canonical.id
            media_item.status = MediaStatus.DOWNLOADED
            job.queued_count -= 1
            job.downloaded_count += 1

    def _fail_job(self, job_id: int, error: Exception) -> None:
        with self.factory.begin() as session:
            job = session.get(DownloadJob, job_id)
            if job is not None:
                job.status = JobStatus.FAILED
                job.last_error = str(error)
                job.completed_at = utc_now()


def run_job(settings: Settings, job_id: int) -> None:
    worker = DownloadWorker(settings)
    try:
        worker.run(job_id)
    finally:
        worker.close()
