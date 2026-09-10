"""HTML routes for creating and inspecting downloader jobs."""

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from social_media_toolkit.config import Category
from social_media_toolkit.database.models import DownloadJob, JobStatus, SourceAccount
from social_media_toolkit.downloader.jobs import create_download_job
from social_media_toolkit.downloader.worker import run_job
from social_media_toolkit.integrations.instagram import parse_profile_url


router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))


def recent_jobs(request: Request) -> list[tuple[DownloadJob, SourceAccount]]:
    factory = request.app.state.session_factory
    with factory() as session:
        statement = (
            select(DownloadJob, SourceAccount)
            .join(SourceAccount)
            .order_by(DownloadJob.created_at.desc())
            .limit(25)
        )
        return list(session.execute(statement).tuples())


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "categories": list(Category),
            "default_category": request.app.state.settings.default_category,
            "jobs": recent_jobs(request),
            "error": None,
        },
    )


@router.post("/jobs", response_class=HTMLResponse)
def create_job(
    request: Request,
    background_tasks: BackgroundTasks,
    profile_url: str = Form(),
    category: Category = Form(),
) -> HTMLResponse:
    try:
        profile = parse_profile_url(profile_url)
    except ValueError as error:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "categories": list(Category),
                "default_category": category,
                "jobs": recent_jobs(request),
                "error": str(error),
            },
            status_code=422,
        )

    job_id = create_download_job(
        request.app.state.session_factory,
        profile.canonical_url,
        category,
    )
    if request.app.state.settings.auto_start_jobs:
        background_tasks.add_task(
            run_job,
            request.app.state.settings,
            job_id,
        )

    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_details(request: Request, job_id: int) -> HTMLResponse:
    factory = request.app.state.session_factory
    with factory() as session:
        row = session.execute(
            select(DownloadJob, SourceAccount)
            .join(SourceAccount)
            .where(DownloadJob.id == job_id)
        ).one_or_none()

    if row is None:
        return templates.TemplateResponse(
            request,
            "not_found.html",
            {"job_id": job_id},
            status_code=404,
        )

    job, account = row
    return templates.TemplateResponse(
        request,
        "job.html",
        {"job": job, "account": account},
    )


@router.post("/jobs/{job_id}/run")
def start_job(
    request: Request,
    job_id: int,
    background_tasks: BackgroundTasks,
) -> RedirectResponse:
    factory = request.app.state.session_factory
    with factory() as session:
        job = session.get(DownloadJob, job_id)
        runnable = job is not None and job.status in {
            JobStatus.QUEUED,
            JobStatus.FAILED,
        }
    if runnable:
        background_tasks.add_task(run_job, request.app.state.settings, job_id)
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)
