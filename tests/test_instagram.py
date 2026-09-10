from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from social_media_toolkit.integrations.instagram import (
    InstaloaderClient,
    parse_profile_url,
)


def test_parse_profile_url_normalizes_username_and_host() -> None:
    profile = parse_profile_url("instagram.com/Example.User/")

    assert profile.username == "example.user"
    assert profile.canonical_url == "https://www.instagram.com/example.user/"

    username_only = parse_profile_url("Example.User")
    assert username_only == profile


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/account/",
        "http://instagram.com/account/",
        "https://instagram.com/reel/abc/",
        "https://instagram.com/",
        "instagram.com",
    ],
)
def test_parse_profile_url_rejects_non_profile_urls(value: str) -> None:
    with pytest.raises(ValueError):
        parse_profile_url(value)


def test_post_video_classification_distinguishes_posts_and_reels() -> None:
    post = SimpleNamespace(
        shortcode="ABC123",
        caption="A caption",
        date_utc=datetime(2026, 9, 10, tzinfo=timezone.utc),
        typename="GraphVideo",
        is_video=True,
        video_url="https://cdn.example/video.mp4",
        mediaid=123,
    )

    regular = list(InstaloaderClient._post_videos(post, is_reel=False))
    reel = list(InstaloaderClient._post_videos(post, is_reel=True))

    assert regular[0].media_type == "video"
    assert regular[0].permalink == "https://www.instagram.com/p/ABC123/"
    assert reel[0].media_type == "reel"
    assert reel[0].permalink == "https://www.instagram.com/reel/ABC123/"


def test_post_videos_selects_only_video_children_from_a_carousel() -> None:
    post = SimpleNamespace(
        shortcode="CAROUSEL",
        caption=None,
        date_utc=datetime(2026, 9, 10, tzinfo=timezone.utc),
        typename="GraphSidecar",
        mediaid=456,
        get_sidecar_nodes=lambda: iter(
            [
                SimpleNamespace(is_video=False, video_url=None),
                SimpleNamespace(
                    is_video=True,
                    video_url="https://cdn.example/carousel.mp4",
                ),
            ]
        ),
    )

    videos = list(InstaloaderClient._post_videos(post, is_reel=False))

    assert len(videos) == 1
    assert videos[0].platform_media_id == "456:1"
    assert videos[0].item_index == 1
    assert videos[0].media_type == "carousel_video"
