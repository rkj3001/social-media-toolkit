from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from social_media_toolkit.config import Category, Settings
from social_media_toolkit.database.migrate import upgrade_database
from social_media_toolkit.database.models import (
    CanonicalMedia,
    DownloadJob,
    JobStatus,
    MediaStatus,
    SourcePost,
    SourceMediaItem,
)
from social_media_toolkit.database.session import (
    create_database_engine,
    create_session_factory,
)
from social_media_toolkit.downloader.jobs import create_download_job
from social_media_toolkit.downloader.worker import DownloadWorker
from social_media_toolkit.integrations.instagram import InstagramVideo


class FakeInstagramClient:
    def __init__(self, videos: list[InstagramVideo], payload: bytes) -> None:
        self.videos = videos
        self.payload = payload
        self.download_count = 0

    def discover_videos(self, _username: str) -> Iterator[InstagramVideo]:
        yield from self.videos

    def download_video(self, _video: InstagramVideo, destination: Path) -> None:
        self.download_count += 1
        destination.write_bytes(self.payload)


def video(media_id: str, shortcode: str) -> InstagramVideo:
    return InstagramVideo(
        platform_media_id=media_id,
        shortcode=shortcode,
        permalink=f"https://www.instagram.com/p/{shortcode}/",
        caption=f"Caption for {shortcode}",
        published_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        media_type="reel",
        item_index=0,
        video_url=f"https://cdn.example/{shortcode}.mp4",
    )


def test_worker_hashes_cross_account_duplicates_before_final_storage(
    tmp_path: Path,
) -> None:
    settings = Settings(media_library_root=tmp_path, auto_start_jobs=False)
    upgrade_database(settings)
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)

    first_job = create_download_job(factory, "instagram.com/dogs", Category.DOG)
    second_job = create_download_job(factory, "instagram.com/pets", Category.CAT)
    payload = b"video bytes with an embedded audio track"

    first_client = FakeInstagramClient([video("1001", "DOGS1")], payload)
    first_worker = DownloadWorker(settings, first_client)
    second_worker = DownloadWorker(
        settings,
        FakeInstagramClient([video("2002", "PETS2")], payload),
    )
    try:
        first_worker.run(first_job)
        second_worker.run(second_job)
    finally:
        first_worker.close()
        second_worker.close()

    with factory() as session:
        jobs = list(
            session.scalars(select(DownloadJob).order_by(DownloadJob.id))
        )
        items = list(
            session.scalars(select(SourceMediaItem).order_by(SourceMediaItem.id))
        )
        posts = list(session.scalars(select(SourcePost).order_by(SourcePost.id)))
        canonical_count = session.scalar(
            select(func.count()).select_from(CanonicalMedia)
        )
        canonical = session.scalar(select(CanonicalMedia))

    assert [job.status for job in jobs] == [
        JobStatus.COMPLETED,
        JobStatus.COMPLETED,
    ]
    assert jobs[0].downloaded_count == 1
    assert jobs[1].duplicate_count == 1
    assert [job.queued_count for job in jobs] == [0, 0]
    assert [item.status for item in items] == [
        MediaStatus.DOWNLOADED,
        MediaStatus.DUPLICATE,
    ]
    assert items[0].canonical_media_id == items[1].canonical_media_id
    assert [post.caption for post in posts] == [
        "Caption for DOGS1",
        "Caption for PETS2",
    ]
    assert canonical_count == 1
    assert canonical is not None
    assert (tmp_path / canonical.relative_path).read_bytes() == payload
    assert first_client.download_count == 1
    engine.dispose()


def test_worker_skips_an_already_downloaded_source_before_transfer(
    tmp_path: Path,
) -> None:
    settings = Settings(media_library_root=tmp_path, auto_start_jobs=False)
    upgrade_database(settings)
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    discovered_video = video("1001", "DOGS1")

    initial_job = create_download_job(factory, "dogs", Category.DOG)
    initial_client = FakeInstagramClient([discovered_video], b"original")
    retry_client = FakeInstagramClient([discovered_video], b"must not be written")
    initial_worker = DownloadWorker(settings, initial_client)
    retry_worker = DownloadWorker(settings, retry_client)
    try:
        initial_worker.run(initial_job)
        retry_job = create_download_job(factory, "dogs", Category.DOG)
        retry_worker.run(retry_job)
    finally:
        initial_worker.close()
        retry_worker.close()

    with factory() as session:
        retried = session.get(DownloadJob, retry_job)
        canonical = session.scalar(select(CanonicalMedia))

    assert retried is not None
    assert retried.status == JobStatus.COMPLETED
    assert retried.duplicate_count == 1
    assert retry_client.download_count == 0
    assert canonical is not None
    assert (tmp_path / canonical.relative_path).read_bytes() == b"original"
    engine.dispose()
