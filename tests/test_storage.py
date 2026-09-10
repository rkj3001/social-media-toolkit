from pathlib import Path

import pytest

from social_media_toolkit.storage import LibraryStorage


def test_initialize_creates_runtime_directories(tmp_path: Path) -> None:
    storage = LibraryStorage(tmp_path)

    storage.initialize()

    assert all((tmp_path / name).is_dir() for name in storage.DIRECTORIES)


def test_resolve_relative_rejects_path_escape(tmp_path: Path) -> None:
    storage = LibraryStorage(tmp_path)

    with pytest.raises(ValueError, match="inside"):
        storage.resolve_relative(Path("..") / "outside.mp4")


def test_initialize_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="does not exist"):
        LibraryStorage(tmp_path / "missing").initialize()

