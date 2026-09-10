"""CLI for creating and immediately processing one profile download job."""

import argparse

from sqlalchemy import inspect

from social_media_toolkit.config import Category, Settings
from social_media_toolkit.database.models import DownloadJob, JobStatus
from social_media_toolkit.database.session import (
    create_database_engine,
    create_session_factory,
)
from social_media_toolkit.downloader.jobs import create_download_job
from social_media_toolkit.downloader.worker import run_job
from social_media_toolkit.storage import LibraryStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download public Instagram videos into the local media library."
    )
    parser.add_argument("profile", help="Instagram profile URL or username")
    parser.add_argument(
        "--category",
        choices=[category.value for category in Category],
        default=Category.UNCATEGORIZED.value,
    )
    arguments = parser.parse_args()

    settings = Settings()  # type: ignore[call-arg]
    LibraryStorage(settings.media_library_root).initialize()
    engine = create_database_engine(settings)
    try:
        if not inspect(engine).has_table("source_media_items"):
            parser.error("database is not ready; run `smt-migrate` first")
        factory = create_session_factory(engine)
        job_id = create_download_job(
            factory,
            arguments.profile,
            Category(arguments.category),
        )
    finally:
        engine.dispose()

    print(f"Created download job {job_id}.")
    run_job(settings, job_id)
    engine = create_database_engine(settings)
    try:
        factory = create_session_factory(engine)
        with factory() as session:
            job = session.get(DownloadJob, job_id)
            if (
                job is None
                or job.status != JobStatus.COMPLETED
                or job.failed_count > 0
            ):
                detail = job.last_error if job is not None else "job disappeared"
                raise SystemExit(
                    f"Download job {job_id} did not fully succeed: "
                    f"{detail or f'{job.failed_count} media item(s) failed'}"
                )
            print(
                f"Completed job {job_id}: {job.downloaded_count} downloaded, "
                f"{job.duplicate_count} duplicates, {job.failed_count} failed."
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
