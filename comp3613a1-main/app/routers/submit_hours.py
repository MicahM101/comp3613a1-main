from datetime import date

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.submission import (
    StudentRepository,
    SubmissionRepository,
    VolunteerCauseRepository,
)
from app.services.submission import SubmissionService
from app.utilities.flash import flash
from . import router, templates


def _service(db: SessionDep) -> SubmissionService:
    return SubmissionService(
        SubmissionRepository(db),
        VolunteerCauseRepository(db),
        StudentRepository(db),
    )


@router.get("/app/hours/new", response_class=HTMLResponse)
async def submit_hours_form(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    service = _service(db)
    return templates.TemplateResponse(
        request=request,
        name="submit_form.html",
        context={
            "user": user,
            "causes": service.list_causes(),
        },
    )


@router.post("/app/hours/new", response_class=HTMLResponse)
async def submit_hours_preview(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    cause_id: int = Form(...),
    hours: float = Form(...),
    served_on: date = Form(...),
    time_of_day: str = Form(...),
    meridiem: str = Form(...),
    document: UploadFile = File(...),
):
    """Validate + store the upload, then show the confirmation screen."""
    service = _service(db)
    cause = service.causes.get_by_id(cause_id)

    if hours <= 0:
        flash(request, "Hours served must be more than zero.", "warning")
        return templates.TemplateResponse(
            request=request,
            name="submit_form.html",
            context={"user": user, "causes": service.list_causes()},
        )

    try:
        document_path = service.save_document(document)
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return templates.TemplateResponse(
            request=request,
            name="submit_form.html",
            context={"user": user, "causes": service.list_causes()},
        )

    return templates.TemplateResponse(
        request=request,
        name="submit_confirm.html",
        context={
            "user": user,
            "cause": cause,
            "hours": hours,
            "date_completed": served_on,
            "start_time": f"{time_of_day} {meridiem}",
            "document_path": document_path,
            "document_name": document.filename or "document",
        },
    )


@router.post("/app/hours/confirm")
async def submit_hours_confirm(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    cause_id: int = Form(...),
    hours: float = Form(...),
    date_completed: date = Form(...),
    start_time: str = Form(...),
    document_path: str = Form(...),
):
    """Record the confirmed submission and return to the Account page."""

    service = _service(db)

    service.record_submission(
        user=user,
        cause_id=cause_id,
        hours=hours,
        date_completed=date_completed,
        start_time=start_time,
        document_path=document_path,
    )

    flash(request, "Your volunteer hours have been submitted successfully.", "success")

    return RedirectResponse(url=request.url_for("user_home_view"), status_code=303)
