"""Run Alembic migrations against the configured external-drive database."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from social_media_toolkit.config import Settings
from social_media_toolkit.storage import LibraryStorage


def upgrade_database(settings: Settings) -> None:
    LibraryStorage(settings.media_library_root).initialize()

    repository_root = Path(__file__).resolve().parents[3]
    config = Config(repository_root / "alembic.ini")
    config.set_main_option("script_location", str(repository_root / "migrations"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")


def main() -> None:
    upgrade_database(Settings())  # type: ignore[call-arg]


if __name__ == "__main__":
    main()

