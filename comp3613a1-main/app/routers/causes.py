from fastapi import Query, Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.submission import VolunteerCauseRepository
from app.services.cause_service import CauseService
from . import router, templates


@router.get("/causes", response_class=HTMLResponse)
async def causes_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    q: str = Query(""),
):
    """Every cause a student can serve (the same list feeds the submission form)."""
    service = CauseService(VolunteerCauseRepository(db))

    return templates.TemplateResponse(
        request=request,
        name="causes.html",
        context={"user": user, "causes": service.list_causes(search=q), "search": q},
    )
