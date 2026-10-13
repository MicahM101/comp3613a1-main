from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.admin import AdminRepository
from app.repositories.submission import (
    StudentRepository,
    SubmissionRepository,
    VolunteerCauseRepository,
)
from app.services.review_service import ReviewService
from app.utilities.flash import flash
from . import router, templates


def _review_service(db: SessionDep) -> ReviewService:
    return ReviewService(
        SubmissionRepository(db),
        VolunteerCauseRepository(db),
        StudentRepository(db),
        AdminRepository(db),
    )


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    """Workflow 2 — the pending queue, searchable from the wireframe's box."""
    search = request.query_params.get("q", "").strip()
    service = _review_service(db)

    return templates.TemplateResponse(
        request=request,
        name="admin_queue.html",
        context={
            "user": user,
            "rows": service.queue(search),
            "search": search,
        },
    )


@router.get("/admin/submissions/{submission_id}", response_class=HTMLResponse)
async def submission_review_view(
    request: Request,
    submission_id: int,
    user: AdminDep,
    db: SessionDep,
):
    """The review card: student details, the hours, and the document link."""
    service = _review_service(db)
    detail = service.review_detail(submission_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    return templates.TemplateResponse(
        request=request,
        name="admin_review.html",
        context={"user": user, "detail": detail},
    )


@router.get("/admin/submissions/{submission_id}/decision/{state}", response_class=HTMLResponse)
async def submission_decision_confirm(
    request: Request,
    submission_id: int,
    state: str,
    user: AdminDep,
    db: SessionDep,
):
    """The 'Approve student's Hours?' / 'Reject…' confirmation screen."""
    service = _review_service(db)
    detail = service.review_detail(submission_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if state not in ("approved", "rejected"):
        raise HTTPException(status_code=404, detail="Unknown decision")

    return templates.TemplateResponse(
        request=request,
        name="admin_confirm.html",
        context={"user": user, "detail": detail, "state": state},
    )


@router.post("/admin/submissions/{submission_id}/decision")
async def submission_decision_apply(
    request: Request,
    submission_id: int,
    user: AdminDep,
    db: SessionDep,
    state: str = Form(...),

):
    """TODO(student): complete this handler.

    Keep the route thin: build the review service, ask it to record this
    decision for the signed-in admin, then send the browser back to the
    Submissions queue with a confirmation message.

    The service owns the checks (unknown decision, missing submission,
    already reviewed) — it raises ValueError for those, so catch it and flash
    the message instead of letting the request fail.
    """
    service = _review_service(db)
    try:
        service.decide(submission_id = submission_id, state = state, user = user)
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(
            url="/admin",
            status_code=303,
        )

    flash(request,
          f"Submission {state} successfully.",
          "success",
    )

    return RedirectResponse(
        url="/admin",
        status_code=303,
    )