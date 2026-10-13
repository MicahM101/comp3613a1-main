from datetime import date

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.models.user import User
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


def _student_only(request: Request, user: User) -> RedirectResponse | None:
    """Hours belong to students — send an admin back to their own queue."""
    if user.role == "admin":
        flash(request, "Hours are submitted from a student account.", "warning")
        return RedirectResponse(
            url=request.url_for("admin_home_view"), status_code=303
        )
    return None


@router.get("/app/hours/new", response_class=HTMLResponse)
async def submit_hours_form(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    blocked = _student_only(request, user)
    if blocked:
        return blocked

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
    time_hour: str = Form(...),
    time_minute: str = Form(...),
    meridiem: str = Form(...),
    document: UploadFile = File(...),
):
    """Validate + store the upload, then show the confirmation screen."""
    blocked = _student_only(request, user)
    if blocked:
        return blocked

    service = _service(db)
    cause = service.causes.get_by_id(cause_id)
    start_time = f"{time_hour}:{time_minute} {meridiem}"

    if hours <= 0:
        flash(request, "Hours served must be more than zero.", "warning")
        return templates.TemplateResponse(
            request=request,
            name="submit_form.html",
            context={"user": user, "causes": service.list_causes()},
        )

    try:
        document_path, document_name = service.save_document(document)
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
            "start_time": start_time,
            "document_path": document_path,
            "document_name": document_name,
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
    document_name: str = Form(""),
):
    """Record the confirmed submission and return to the Account page."""
    blocked = _student_only(request, user)
    if blocked:
        return blocked

    service = _service(db)

    service.record_submission(
        user=user,
        cause_id=cause_id,
        hours=hours,
        date_completed=date_completed,
        start_time=start_time,
        document_path=document_path,
        original_document_name=document_name or None,
    )

    flash(request, "Your volunteer hours have been submitted successfully.", "success")

    return RedirectResponse(url=request.url_for("user_home_view"), status_code=303)
