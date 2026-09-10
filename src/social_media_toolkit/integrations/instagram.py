"""Instagram validation and Instaloader-backed media retrieval."""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Protocol
from urllib.parse import urlparse

import instaloader


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]{1,30}$")
RESERVED_PATHS = {"accounts", "direct", "explore", "p", "reel", "reels", "stories"}


@dataclass(frozen=True)
class InstagramProfile:
    username: str
    canonical_url: str


@dataclass(frozen=True)
class InstagramVideo:
    """A downloadable video discovered in a post, Reel, or carousel."""

    platform_media_id: str
    shortcode: str
    permalink: str
    caption: str | None
    published_at: datetime
    media_type: str
    item_index: int
    video_url: str


class InstagramClient(Protocol):
    """Boundary used by the worker and replaced with a fake in tests."""

    def discover_videos(self, username: str) -> Iterator[InstagramVideo]: ...

    def download_video(self, video: InstagramVideo, destination: Path) -> None: ...


class InstaloaderClient:
    """Use Instaloader for public discovery without re-encoding media files."""

    def __init__(self) -> None:
        self.loader = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_video_thumbnails=False,
            save_metadata=False,
            post_metadata_txt_pattern=None,
        )

    def discover_videos(self, username: str) -> Iterator[InstagramVideo]:
        profile = instaloader.Profile.from_username(self.loader.context, username)
        seen_shortcodes: set[str] = set()

        # Instagram may expose a Reel in both iterators, so shortcode is the
        # stable pre-download reservation key.
        for posts, is_reel in (
            (profile.get_reels(), True),
            (profile.get_posts(), False),
        ):
            for post in posts:
                if post.shortcode in seen_shortcodes:
                    continue
                seen_shortcodes.add(post.shortcode)
                yield from self._post_videos(post, is_reel)

    def download_video(self, video: InstagramVideo, destination: Path) -> None:
        """Write the original MP4 bytes so its embedded audio is preserved."""

        response = self.loader.context.get_raw(video.video_url)
        try:
            content_type = response.headers.get("Content-Type", "")
            normalized_type = content_type.lower().split(";", maxsplit=1)[0]
            if normalized_type and normalized_type not in {
                "application/octet-stream",
            } and not normalized_type.startswith("video/"):
                raise ValueError(
                    f"Instagram returned {content_type!r} instead of a video"
                )
            with destination.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
        finally:
            response.close()

    @staticmethod
    def _post_videos(
        post: instaloader.Post,
        is_reel: bool,
    ) -> Iterator[InstagramVideo]:
        common = {
            "shortcode": post.shortcode,
            "permalink": (
                f"https://www.instagram.com/reel/{post.shortcode}/"
                if is_reel
                else f"https://www.instagram.com/p/{post.shortcode}/"
            ),
            "caption": post.caption,
            "published_at": post.date_utc,
        }
        if post.typename == "GraphSidecar":
            for index, node in enumerate(post.get_sidecar_nodes()):
                if node.is_video and node.video_url:
                    yield InstagramVideo(
                        platform_media_id=f"{post.mediaid}:{index}",
                        media_type="carousel_video",
                        item_index=index,
                        video_url=node.video_url,
                        **common,
                    )
        elif post.is_video and post.video_url:
            yield InstagramVideo(
                platform_media_id=str(post.mediaid),
                media_type="reel" if is_reel else "video",
                item_index=0,
                video_url=post.video_url,
                **common,
            )


def parse_profile_url(value: str) -> InstagramProfile:
    """Return a canonical public-profile reference or raise a useful error."""

    raw_value = value.strip()
    if raw_value.lower() in {"instagram.com", "www.instagram.com"}:
        raw_value = f"https://{raw_value}"
    if USERNAME_PATTERN.fullmatch(raw_value):
        username = raw_value.lower()
        if username in RESERVED_PATHS:
            raise ValueError("Instagram profile contains a reserved name")
        return InstagramProfile(
            username=username,
            canonical_url=f"https://www.instagram.com/{username}/",
        )
    if "://" not in raw_value:
        raw_value = f"https://{raw_value}"

    parsed = urlparse(raw_value)
    if parsed.scheme != "https":
        raise ValueError("Instagram profile URL must use HTTPS")

    hostname = (parsed.hostname or "").lower()
    if hostname not in {"instagram.com", "www.instagram.com"}:
        raise ValueError("Enter a profile URL from instagram.com")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 1:
        raise ValueError("Enter an Instagram profile URL, not a post or Reel URL")

    username = parts[0].lower()
    if username in RESERVED_PATHS or not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Instagram profile URL contains an invalid username")

    return InstagramProfile(
        username=username,
        canonical_url=f"https://www.instagram.com/{username}/",
    )
