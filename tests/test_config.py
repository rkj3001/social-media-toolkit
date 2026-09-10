from pathlib import Path

import pytest
from pydantic import ValidationError

from social_media_toolkit.config import Settings


def test_settings_build_database_path_under_library_root(tmp_path: Path) -> None:
    settings = Settings(media_library_root=tmp_path)

    assert settings.database_path == tmp_path / "library.db"


def test_settings_reject_non_loopback_host(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="loopback"):
        Settings(media_library_root=tmp_path, app_host="0.0.0.0")

