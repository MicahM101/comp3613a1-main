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
    service = SubmissionService(
        SubmissionRepository(db),
        VolunteerCauseRepository(db),
        StudentRepository(db),
    )
    student = service.get_student_for(user)

    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={
            "user": user,
            "contributions": service.recent_contributions(student.id),
            "total_hours": service.total_hours_earned(student.id),
        },
    )
