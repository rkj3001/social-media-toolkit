# Roadmap

## Phase 0: Project foundation

- Create the GitHub-ready repository structure.
- Agree on scope, software, storage layout, and application boundaries.
- Select a replaceable Instagram retrieval adapter.

## Phase 1: Downloader foundation

- [x] Add Python packaging and development commands.
- [x] Implement typed configuration and external-drive availability checks.
- [x] Create initial SQLite models and migrations.
- [x] Add localhost pages for sources and download jobs.
- [x] Add source-post, source-media, and canonical-media models.
- [x] Add an Instaloader-backed worker shared by the CLI and UI.

## Phase 2: Discovery and downloading

- [x] Validate source profile URLs and username-only CLI input.
- [x] Discover public Reels, video posts, and carousel video children.
- [x] Store source posts and captions.
- [x] Download to temporary files and atomically finalize successful files.
- [ ] Add durable job resumption and explicit rate-limit handling.

## Phase 3: Duplicate detection

- [x] Enforce source media ID and shortcode uniqueness.
- [x] Add SHA-256 exact matching.
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
