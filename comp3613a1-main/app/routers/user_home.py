from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.submission import (
    StudentRepository,
    SubmissionRepository,
    VolunteerCauseRepository,
)
from app.services.submission import SubmissionService
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    """Account page: the student's hours dashboard, or the admin's profile."""

    if user.role == "admin":
        # An admin has no Student row and nothing to submit. The wireframe's
        # Account tab still needs somewhere to land, so it shows the profile.
        return templates.TemplateResponse(
            request=request,
            name="admin_account.html",
            context={"user": user},
        )

    service = SubmissionService(
        SubmissionRepository(db),
        VolunteerCauseRepository(db),
        StudentRepository(db),
    )

    # get_student_for also creates the profile on first sign-in, so it has to
    # be the first call — the other three need a student id.
    student = service.get_student_for(user)

    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={
            "user": user,
            "contributions": service.recent_contributions(student.id),
            "total_hours": service.total_hours_earned(student.id),
            "submissions": service.my_submissions(student.id),
        },
    )
