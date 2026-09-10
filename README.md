# Social Media Toolkit

Social Media Toolkit is a personal, local-first umbrella project for collecting,
organizing, reviewing, and eventually publishing media across social platforms.
The project is intentionally split into small applications so each capability can
evolve independently without turning the first release into a large system.

## Current focus

Phase 1 is the **Downloader** application: a localhost UI that accepts one or more
public Instagram profile URLs, discovers supported posts and Reels, downloads
videos with their embedded audio, preserves captions and source metadata, and
avoids storing duplicate media.

Instagram access must use methods permitted by Meta and the account owner. Public
availability does not grant permission to scrape, republish, or monetize content.
The implementation must not bypass authentication, rate limits, CAPTCHAs, access
controls, or platform restrictions.

## Applications

| Application | Purpose | Status |
| --- | --- | --- |
| [Downloader](apps/downloader/README.md) | Discover and download supported media into the local library | Phase 1 |
| [Library](apps/library/README.md) | Browse, classify, search, and review duplicates | Planned |
| [Publisher](apps/publisher/README.md) | Prepare and publish approved content through supported platform APIs | Future |

## Repository layout

```text
social-media-toolkit/
  apps/
    downloader/
    library/
    publisher/
  packages/
    database/
    deduplication/
    media-processing/
    storage/
  integrations/
    instagram/
    facebook/
    tiktok/
    youtube/
  docs/
    architecture.md
    roadmap.md
    software-requirements.md
  .github/
    skills/
      social-media-toolkit/
        SKILL.md
  .env.example
  .gitignore
```

The repository contains source code, tests, configuration examples, and
documentation. Downloaded videos, credentials, session data, logs, and the live
SQLite database belong on an external hard drive and must never be committed.

## External-drive library

Every device sets its own `MEDIA_LIBRARY_ROOT`:

```text
SocialMediaLibrary/
  library.db
  media/
    dog/
    cat/
    entertainment/
    uncategorized/
  metadata/
  thumbnails/
  temporary/
  logs/
```

Paths stored in the database will be relative to `MEDIA_LIBRARY_ROOT`, allowing
the same drive to appear as `E:\` on one computer and `F:\` on another.

Only one application instance should write to the external-drive SQLite database
at a time. The application will refuse to download when the configured drive is
missing.

## Planned localhost experience

The initial UI will run only on the local computer and provide:

1. A source form for an Instagram profile URL and category.
2. A job screen showing discovery, queued downloads, skips, failures, and retries.
3. A library screen showing saved videos, captions, sources, and duplicates.
4. Categories including `dog`, `cat`, `entertainment`, and `uncategorized`.

## Duplicate prevention

Duplicate detection will happen at multiple levels:

1. Instagram media ID and shortcode before downloading.
2. SHA-256 after downloading to a temporary file.
3. Duration and perceptual frame fingerprints for reposted or re-encoded videos.

One physical video can have multiple source records so captions and source
accounts are retained without wasting storage.

## Development status

The Downloader foundation is runnable. It includes the localhost job UI, a
terminal command, Instaloader-backed video discovery, SQLite source metadata,
external-drive storage, and SHA-256 exact deduplication. Audio inspection and
perceptual matching remain planned; see [docs/roadmap.md](docs/roadmap.md).

See [software requirements](docs/software-requirements.md) before development.

## Copilot project skill

The repository includes
[`.github/skills/social-media-toolkit/SKILL.md`](.github/skills/social-media-toolkit/SKILL.md).
After cloning the repository on another device, GitHub Copilot CLI can discover
this repository skill. It carries the project scope, architecture, technology
direction, storage invariants, duplicate rules, roadmap boundaries, and
cross-device continuation workflow.

Use `/skills` in Copilot CLI to inspect available skills when needed.
