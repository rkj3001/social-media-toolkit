"""Command-line entry point for the localhost server."""

import uvicorn

from social_media_toolkit.config import Settings
from social_media_toolkit.downloader.app import create_app


def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    uvicorn.run(
        create_app(settings),
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

