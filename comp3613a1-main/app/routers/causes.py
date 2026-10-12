from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.submission import VolunteerCauseRepository
from . import router, templates


@router.get("/causes", response_class=HTMLResponse)
async def causes_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    """Every cause a student can serve (the same list feeds the submission form)."""
    causes = VolunteerCauseRepository(db).list_all()
    return templates.TemplateResponse(
        request=request,
        name="causes.html",
        context={"user": user, "causes": causes},
    )
