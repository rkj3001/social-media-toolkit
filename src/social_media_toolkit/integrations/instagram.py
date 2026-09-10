"""Validation and normalization at the Instagram integration boundary."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]{1,30}$")
RESERVED_PATHS = {"accounts", "direct", "explore", "p", "reel", "reels", "stories"}


@dataclass(frozen=True)
class InstagramProfile:
    username: str
    canonical_url: str


def parse_profile_url(value: str) -> InstagramProfile:
    """Return a canonical public-profile reference or raise a useful error."""

    raw_value = value.strip()
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

