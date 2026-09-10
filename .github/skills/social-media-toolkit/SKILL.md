---
name: social-media-toolkit
description: Work on the Social Media Toolkit local-first umbrella project. Use when planning, implementing, testing, or reviewing its downloader, media library, deduplication, external-drive storage, localhost UI, or future publishing applications.
---

# Social Media Toolkit project skill

Use this skill only inside the Social Media Toolkit repository. It provides the
project's durable context so work can continue consistently after cloning the
repository onto another device.

## Start every task by loading project context

Before planning or editing:

1. Read the root `README.md`.
2. Read `docs/architecture.md`, `docs/roadmap.md`, and
   `docs/software-requirements.md`.
3. Read the README for the application being changed.
4. Read the README files for any shared packages or integrations involved.
5. Inspect the current implementation and tests; documentation describes intent,
   but working code is authoritative when they differ.

Do not start future roadmap phases unless the user explicitly asks for them.

## Project purpose

This is a personal, local-first umbrella project with separate applications:

- **Downloader:** Phase 1. Discover and download supported media, captions, and
  source metadata into an external-drive library.
- **Library:** Browse, classify, preview, and review duplicates.
- **Publisher:** A future, separate application for authorized publishing through
  supported Instagram, TikTok, Facebook, and YouTube APIs.

Keep the project a modular monolith. Do not introduce microservices, Redis,
Celery, Kubernetes, or cloud infrastructure unless requirements later justify
them.

## Current implementation priority

The current focus is the Downloader and the minimum shared packages it requires:

```text
apps/downloader
packages/database
packages/deduplication
packages/media-processing
packages/storage
integrations/instagram
```

Build the smallest complete vertical slice before expanding:

1. Python project and reproducible setup.
2. Typed configuration.
3. External-drive validation.
4. SQLite models and migrations.
5. Localhost source/job UI.
6. Permitted Instagram discovery.
7. Safe downloading and metadata persistence.
8. Exact duplicate detection.
9. Perceptual duplicate review.

## Technology direction

Phase 1 uses:

- Python 3.12 or later.
- FastAPI and Uvicorn.
- Server-rendered Jinja2 templates with minimal browser JavaScript.
- SQLAlchemy and Alembic with SQLite.
- Instaloader behind the Instagram integration boundary for public discovery and
  original media transfer.
- Pydantic Settings for configuration.
- FFmpeg and ffprobe for media inspection and fingerprint frames.
- Pillow and ImageHash for perceptual hashes.
- pytest for tests.

Node.js is not required for Phase 1. Do not add it merely to build the initial
localhost UI.

## Repository and runtime-data boundary

GitHub stores:

- Source code.
- Tests.
- Dependency lock/configuration files.
- Database migrations.
- Documentation and configuration examples.

The external hard drive stores:

- `library.db`.
- Downloaded media.
- Captions and generated metadata.
- Thumbnails and fingerprints.
- Temporary downloads and runtime logs.

Never commit media, live databases, `.env`, cookies, session files, access
tokens, passwords, or other credentials. Preserve and extend `.gitignore` when
new runtime artifacts are introduced.

## Cross-device storage invariants

Use `MEDIA_LIBRARY_ROOT` from per-device configuration. The external drive can
have a different drive letter or mount point on each device.

Persist paths relative to `MEDIA_LIBRARY_ROOT`:

```text
media\dog\example-account\2026\09\shortcode.mp4
```

Do not persist absolute paths such as `E:\SocialMediaLibrary\...`.

The application must:

- Refuse to start storage or download work if the configured root is absent.
- Never silently fall back to an internal drive.
- Prevent resolved paths from escaping the configured root.
- Use temporary `.partial` files followed by atomic finalization.
- Stop safely and retain recoverable job state if the drive disappears.
- Permit only one writer to the external-drive SQLite database at a time.

Do not assume that the hard drive can be used concurrently by two devices.

## Downloader behavior

The localhost UI should initially support:

- Adding an Instagram public profile URL.
- Selecting `dog`, `cat`, `entertainment`, or `uncategorized`.
- Starting and resuming a discovery/download job.
- Viewing discovered, queued, downloaded, duplicate, skipped, and failed counts.
- Viewing actionable failures without exposing credentials.
- Browsing downloaded media and its original source information.

Preserve for every source post:

- Platform account ID and username when available.
- Platform media ID and shortcode.
- Original permalink.
- Original caption.
- Publication and discovery timestamps.
- Media/product type and carousel parent/child relationship.
- Download status and attempts.
- Canonical media relationship.

Captions belong to source-post records because two reposts can have different
descriptions. Categories are local library metadata and are not Instagram fields.

## Duplicate-detection invariants

Detect duplicates in this order:

1. Before network download, check platform media ID and shortcode.
2. Reserve new source IDs using database uniqueness constraints.
3. Download into the external-drive temporary directory.
4. Calculate SHA-256 and reject exact file duplicates.
5. Inspect duration and representative frames for possible re-encoded reposts.
6. Link duplicate source posts to one canonical physical media file.

Do not discard source metadata when media is duplicated. Keep all source URLs and
captions linked to the canonical file.

Start with strict exact matching. Perceptual matches should go to a review queue
until thresholds are validated with representative samples; do not automatically
delete uncertain matches.

## Instagram and rights boundaries

Instagram retrieval currently uses Instaloader as a replaceable Python
dependency. It is unofficial and may break when Instagram changes its site.
Keep all Instaloader-specific code behind the integration boundary.

Do not implement:

- Authentication or login bypass.
- CAPTCHA solving or bypass.
- Rate-limit evasion.
- New private API reverse engineering outside the Instaloader dependency.
- Access-control circumvention.
- Proxy rotation intended to avoid platform enforcement.

Surface unsupported access plainly in the UI. Public availability does not grant
redistribution or commercial rights. Preserve source and permission/license
metadata needed for later review. Never automatically send downloaded media to
the future Publisher.

## Engineering rules

- Keep application boundaries clear but reuse shared packages.
- Search for existing helpers before adding new ones.
- Use typed models and explicit error states.
- Do not swallow discovery, download, storage, or database errors.
- Make jobs idempotent and resumable.
- Use database transactions and uniqueness constraints for concurrency safety.
- Add focused tests with every behavior change.
- Update the relevant application/package README when behavior or setup changes.
- Keep the localhost server bound to `127.0.0.1` by default.
- Do not expose the UI to a network without authentication and an explicit user
  request.

## Cross-device continuation workflow

On a newly configured device:

1. Clone the GitHub repository and check out `main`.
2. Install the software listed in `docs/software-requirements.md`.
3. Create the Python virtual environment and install locked dependencies.
4. Copy `.env.example` to `.env`.
5. Set `MEDIA_LIBRARY_ROOT` to the connected external-drive library.
6. Confirm the drive and `library.db` are available before starting.
7. Run migrations only through the repository's documented migration command.
8. Start the localhost application using the documented project command.

If setup or run commands have not yet been implemented, add and document them as
part of the relevant foundation milestone instead of inventing commands in user
instructions.

## Decisions that require user confirmation

Ask before implementing when a task depends on an unresolved product choice:

- Whether image-only Instagram posts are in Phase 1.
- Whether optional local Instaloader session login should be added.
- Whether a perceptual match should be skipped or manually reviewed.
- Whether a newly requested feature belongs in Downloader, Library, or Publisher.
- Whether support beyond Windows is required now.

Do not block routine implementation on choices already established in the
repository documentation.
