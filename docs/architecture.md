# Architecture

## Principles

- Local-first: the UI and workers run on the user's computer.
- External-drive storage: generated data stays outside Git and travels between
  devices on the drive.
- Modular monolith: applications share packages without requiring microservices.
- Database-first job tracking: every discovered item and state transition is
  recorded.
- Rights-aware: source and permission metadata is retained for future review.

## Phase 1 components

```text
Browser on localhost
        |
        v
Downloader web application
        |
        +--> Instagram integration
        |
        +--> Discovery/download job runner
        |
        +--> SQLite on external drive
        |
        +--> Deduplication and media processing
        |
        +--> Media files on external drive
```

The first implementation will be one Python process. A separate queue service,
Redis, containers, and cloud infrastructure are intentionally excluded.

## Suggested data model

### accounts

- `id`
- `platform`
- `platform_user_id`
- `username`
- `profile_url`
- `last_sync_at`

### download_jobs

- `id`
- `account_id`
- `category`
- `status`
- `created_at`
- `completed_at`
- counters and last error

### source_posts

- `id`
- `account_id`
- `platform_media_id`
- `shortcode`
- `permalink`
- `caption`
- `published_at`
- `media_type`
- `canonical_media_id`
- `download_status`

### canonical_media

- `id`
- `relative_path`
- `sha256`
- `duration_ms`
- `byte_size`
- `has_audio`
- perceptual frame hashes

### download_attempts

- `id`
- `source_post_id`
- `attempt_number`
- `started_at`
- `completed_at`
- `http_status`
- `error_code`
- `error_message`

## Duplicate workflow

1. Reject an already completed platform media ID or shortcode.
2. Reserve new IDs with a unique database constraint.
3. Download to a temporary file.
4. Compare SHA-256 with canonical media.
5. For different files of similar duration, compare perceptual frame hashes.
6. Link duplicate sources to existing canonical media.
7. Move only unique media into the final category path.

Captions belong to source posts, not canonical media, because reposts may use
different descriptions.

## Portability

Application configuration contains an absolute device path, but persisted file
records are relative:

```text
media\dog\example-account\2026\09\shortcode.mp4
```

This allows the library to move between Windows drive letters and leaves room for
other operating systems later.

