import pytest

from social_media_toolkit.integrations.instagram import parse_profile_url


def test_parse_profile_url_normalizes_username_and_host() -> None:
    profile = parse_profile_url("instagram.com/Example.User/")

    assert profile.username == "example.user"
    assert profile.canonical_url == "https://www.instagram.com/example.user/"


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/account/",
        "http://instagram.com/account/",
        "https://instagram.com/reel/abc/",
        "https://instagram.com/",
    ],
)
def test_parse_profile_url_rejects_non_profile_urls(value: str) -> None:
    with pytest.raises(ValueError):
        parse_profile_url(value)

