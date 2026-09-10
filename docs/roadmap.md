# Roadmap

## Phase 0: Project foundation

- Create the GitHub-ready repository structure.
- Agree on scope, software, storage layout, and application boundaries.
- Confirm permitted Instagram access options before implementation.

## Phase 1: Downloader foundation

- Add Python packaging and development commands.
- Implement typed configuration and external-drive availability checks.
- Create SQLite models and migrations.
- Add localhost pages for sources and download jobs.

## Phase 2: Discovery and downloading

- Validate source profile URLs.
- Implement permitted media discovery and pagination.
- Store source posts and captions.
- Download to temporary files and atomically finalize successful files.
- Add resumable jobs, retries, and rate-limit handling.

## Phase 3: Duplicate detection

- Enforce media ID and shortcode uniqueness.
- Add SHA-256 exact matching.
- Extract duration and representative frames with FFmpeg.
- Add a possible-duplicate review queue.

## Phase 4: Library

- Browse and preview media.
- Filter by category and source.
- Edit categories.
- Review duplicates and associated captions.

## Future: Publisher

- Add destination accounts and publishing queues.
- Integrate supported platform publishing APIs.
- Add caption editing and scheduling.
- Track rights/permission approval before publishing.

