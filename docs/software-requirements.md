# Software Requirements

## Required for development

| Software | Purpose |
| --- | --- |
| Git | Version control and GitHub synchronization |
| Python 3.12 or later | Backend, jobs, database, and localhost server |
| FFmpeg and ffprobe | Validate media, inspect audio, and create fingerprints |
| A modern browser | Use the localhost interface |
| External hard drive | Store the live database and downloaded media |

## Planned Python libraries

The exact versions will be locked when implementation starts.

| Library | Purpose |
| --- | --- |
| FastAPI | Local HTTP application and API |
| Uvicorn | Local development server |
| Jinja2 | Simple server-rendered UI |
| SQLAlchemy | SQLite models and queries |
| Alembic | Database migrations |
| HTTPX | Authorized HTTP/API requests |
| Pydantic Settings | Typed environment configuration |
| Pillow and ImageHash | Perceptual frame hashes |
| pytest | Automated tests |

## Node.js

Node.js is **not required for Phase 1**. The initial UI will use server-rendered
HTML and small amounts of browser JavaScript. Node.js may be introduced later only
if the Library or Publisher needs a richer frontend.

## GitHub

A free GitHub repository is sufficient. GitHub stores code and documentation, not
the media library. Git Large File Storage is not needed because media files must
remain on the external drive.

## Per-device configuration

Copy `.env.example` to `.env` and set the external-drive path. `.env` and any
authentication/session material remain local to the device.

