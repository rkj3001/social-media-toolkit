"""HTML routes for creating and inspecting downloader jobs."""

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from social_media_toolkit.config import Category
from social_media_toolkit.database.models import DownloadJob, SourceAccount
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

    factory = request.app.state.session_factory
    with factory.begin() as session:
        account = session.scalar(
            select(SourceAccount).where(
                SourceAccount.platform == "instagram",
                SourceAccount.username == profile.username,
            )
        )
        if account is None:
            account = SourceAccount(
                platform="instagram",
                username=profile.username,
                profile_url=profile.canonical_url,
            )
            session.add(account)
            try:
                session.flush()
            except IntegrityError:
                # A concurrent request may have inserted the account first.
                session.rollback()
                with factory.begin() as retry_session:
                    account = retry_session.scalar(
                        select(SourceAccount).where(
                            SourceAccount.platform == "instagram",
                            SourceAccount.username == profile.username,
                        )
                    )
                    if account is None:
                        raise
                    job = DownloadJob(account_id=account.id, category=category)
                    retry_session.add(job)
                    retry_session.flush()
                    job_id = job.id
                return RedirectResponse(f"/jobs/{job_id}", status_code=303)

        job = DownloadJob(account_id=account.id, category=category)
        session.add(job)
        session.flush()
        job_id = job.id

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

