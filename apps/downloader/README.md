# Downloader

The Downloader is the first application in Social Media Toolkit. It will run as a
localhost web application and create an organized, deduplicated media library on
an external hard drive.

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

## Open decisions before implementation

- Which Instagram access method is permitted and technically available for the
  intended accounts.
- Whether Phase 1 includes image-only posts or videos only.
- Whether likely perceptual duplicates are skipped automatically or sent to a
  review queue.
- Supported development operating systems beyond Windows.

