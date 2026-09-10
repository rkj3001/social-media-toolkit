"""Create download jobs consistently from the CLI and localhost UI."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from social_media_toolkit.config import Category
from social_media_toolkit.database.models import DownloadJob, SourceAccount
from social_media_toolkit.integrations.instagram import parse_profile_url


def create_download_job(
    factory: sessionmaker[Session],
    profile_url: str,
    category: Category,
) -> int:
    profile = parse_profile_url(profile_url)
    try:
        with factory.begin() as session:
            account = session.scalar(
                select(SourceAccount).where(
                    SourceAccount.platform == "instagram",
                    SourceAccount.username == profile.username,
                )
            )
            if account is None:
                account = SourceAccount(
                    platform="instagram",
                    username=profile.username,
                    profile_url=profile.canonical_url,
                )
                session.add(account)
                session.flush()

            job = DownloadJob(account_id=account.id, category=category)
            session.add(job)
            session.flush()
            return job.id
    except IntegrityError:
        # Retry the complete transaction if another request created the account.
        with factory.begin() as session:
            account = session.scalar(
                select(SourceAccount).where(
                    SourceAccount.platform == "instagram",
                    SourceAccount.username == profile.username,
                )
            )
            if account is None:
                raise
            job = DownloadJob(account_id=account.id, category=category)
            session.add(job)
            session.flush()
            return job.id
