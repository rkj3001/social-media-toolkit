"""Safe path handling for the external media library."""

from pathlib import Path


class LibraryStorage:
    """Owns the directory layout beneath a configured external-drive root."""

    DIRECTORIES = (
        "media",
        "metadata",
        "thumbnails",
        "temporary",
        "logs",
    )

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()

    def initialize(self) -> None:
        """Validate the configured root and create only its known child folders."""

        if not self.root.exists():
            raise RuntimeError(
                f"MEDIA_LIBRARY_ROOT does not exist: {self.root}. "
                "Connect the drive or correct .env."
            )
        if not self.root.is_dir():
            raise RuntimeError(f"MEDIA_LIBRARY_ROOT is not a directory: {self.root}")

        for directory in self.DIRECTORIES:
            (self.root / directory).mkdir(exist_ok=True)

    def resolve_relative(self, relative_path: str | Path) -> Path:
        """Resolve a stored relative path without allowing escape from the root."""

        candidate = (self.root / relative_path).resolve()
        if not candidate.is_relative_to(self.root):
            raise ValueError("Library path must remain inside MEDIA_LIBRARY_ROOT")
        return candidate

