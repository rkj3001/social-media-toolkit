from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from social_media_toolkit.config import Settings
from social_media_toolkit.database.migrate import upgrade_database
from social_media_toolkit.database.models import DownloadJob, SourceAccount
from social_media_toolkit.database.session import (
    create_database_engine,
    create_session_factory,
)
from social_media_toolkit.downloader.app import create_app


def create_test_settings(tmp_path: Path) -> Settings:
    return Settings(media_library_root=tmp_path)


def test_home_page_and_job_creation(tmp_path: Path) -> None:
    settings = create_test_settings(tmp_path)
    upgrade_database(settings)

    with TestClient(create_app(settings)) as client:
        home = client.get("/")
        response = client.post(
            "/jobs",
            data={
                "profile_url": "https://instagram.com/Funny.Dogs/",
                "category": "dog",
            },
            follow_redirects=False,
        )

    assert home.status_code == 200
    assert "Create a download job" in home.text
    assert response.status_code == 303
    assert response.headers["location"] == "/jobs/1"

    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    with factory() as session:
        account = session.scalar(select(SourceAccount))
        job = session.scalar(select(DownloadJob))

    assert account is not None
    assert account.username == "funny.dogs"
    assert job is not None
    assert job.category.value == "dog"
    engine.dispose()


def test_invalid_profile_is_shown_without_creating_job(tmp_path: Path) -> None:
    settings = create_test_settings(tmp_path)
    upgrade_database(settings)

    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/jobs",
            data={
                "profile_url": "https://instagram.com/reel/abc/",
                "category": "entertainment",
            },
        )

    assert response.status_code == 422
    assert "not a post or Reel URL" in response.text

