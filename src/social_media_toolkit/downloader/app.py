"""FastAPI application factory for the localhost downloader UI."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from social_media_toolkit.config import Settings
from social_media_toolkit.database.session import (
    create_database_engine,
    create_session_factory,
)
from social_media_toolkit.downloader.routes import router
from social_media_toolkit.storage import LibraryStorage


def create_app(settings: Settings) -> FastAPI:
    """Build an app with explicit settings so tests never use a real media drive."""

    storage = LibraryStorage(settings.media_library_root)
    engine = create_database_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        storage.initialize()
        if not inspect(engine).has_table("download_jobs"):
            raise RuntimeError(
                "Database schema is missing. Run `smt-migrate` before starting."
            )

        app.state.settings = settings
        app.state.storage = storage
        app.state.session_factory = create_session_factory(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Social Media Toolkit Downloader", lifespan=lifespan)
    assets = Path(__file__).with_name("static")
    app.mount("/static", StaticFiles(directory=assets), name="static")
    app.include_router(router)
    return app

