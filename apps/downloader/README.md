# Downloader

The Downloader is the first application in Social Media Toolkit. It will run as a
localhost web application and create an organized, deduplicated media library on
an external hard drive.

## Current implementation

The first runnable foundation is available:

- Typed per-device configuration.
- External-drive validation with no internal-drive fallback.
- Alembic-managed SQLite source and job tables.
- Instagram profile URL validation and normalization.
- Localhost pages for creating and inspecting categorized jobs.
- Instaloader-backed discovery for public Reels, video posts, and carousel videos.
- Original-byte video transfer, preserving any audio embedded in the source file.
- SHA-256 exact deduplication with all source captions and URLs retained.
- A shared worker used by both the localhost UI and `smt-download` CLI.

## Local setup

Install Python 3.12 or later. FFmpeg is not required for exact downloads yet; it
will be required when audio inspection and perceptual duplicate detection are
implemented.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env` so `MEDIA_LIBRARY_ROOT` points to an existing folder on the external
drive, then initialize the database and start the server:

```powershell
smt-migrate
smt-downloader
```

Open `http://127.0.0.1:8000`. Stop the server before disconnecting the drive.
New UI jobs start in an in-process background task by default. Set
`AUTO_START_JOBS=false` to create queued jobs that you start manually.

The same worker is available from the terminal:

```powershell
smt-download PROFILE_OR_URL --category dog
```

Run tests with:

```powershell
pytest
```

## Phase 1 scope

- Accept one or more public Instagram profile URLs.
- Let the user select `dog`, `cat`, `entertainment`, or `uncategorized`.
- Discover supported Reels, video posts, and video children in carousel posts.
- Preserve the original caption, source account, post URL, timestamps, and IDs.
- Download the video with its embedded audio when access is permitted.
- Avoid exact duplicates and identify likely reposts.
- Resume interrupted jobs without downloading completed items again.
- Display progress, skipped duplicates, and actionable errors in a localhost UI.

## Not in Phase 1

- Publishing to Instagram, TikTok, Facebook, or YouTube.
- Scheduling posts.
- Cloud hosting or multi-user accounts.
- Mobile applications.
- Separate audio-track downloading.
- Bypassing Instagram authentication, access controls, CAPTCHAs, or rate limits.

## Proposed screens

### New download job

```text
Instagram profile URL: [____________________________]
Category:              [dog v]
Download images:       [ ]

[Start discovery]
```

### Job status

```text
Discovered  Queued  Downloaded  Duplicate  Failed
    120       18        93           7         2
```

### Media details

- Preview
- Local category
- Original caption
- Source account and post URL
- Download status
- Duplicate/canonical-video relationship
- File size, duration, and audio presence

## Processing flow

```text
Profile URL
  -> source validation
  -> permitted media discovery and pagination
  -> reserve media ID in SQLite
  -> download to external-drive temporary directory
  -> validate with ffprobe
  -> calculate SHA-256 and frame fingerprints
  -> link duplicate or atomically move unique file
  -> save caption and metadata
```

## Reliability rules

- A database uniqueness constraint reserves a media item before network work.
- Downloads use `.partial` files and atomic moves.
- Temporary media URLs are used immediately and are not treated as permanent.
- Failed jobs retain an error and retry count.
- The application stops safely if the external drive disappears.
- Only one process may write to the SQLite library at a time.
- Credentials and browser/session data are never stored in Git.

## Open decisions

- Whether optional local Instaloader login sessions should be supported for
  content the user is authorized to access.
- Whether Phase 1 includes image-only posts or videos only.
- Whether likely perceptual duplicates are skipped automatically or sent to a
  review queue.
- Supported development operating systems beyond Windows.

Instaloader is an unofficial Instagram client and may stop working when Instagram
changes its site. The application does not bypass login challenges, CAPTCHAs,
access controls, or rate limits.
