from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.submission import VolunteerCauseRepository
from app.services.cause_service import CauseService
from app.utilities.flash import flash

from . import router, templates


def _cause_service(db: SessionDep) -> CauseService:
    return CauseService(VolunteerCauseRepository(db))


@router.get("/admin/causes", response_class=HTMLResponse)
async def admin_causes_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    """The admin's cause page: what each cause still has to give."""
    service = _cause_service(db)

    return templates.TemplateResponse(
        request=request,
        name="admin_causes.html",
        context={"user": user, "causes": service.list_causes()},
    )


@router.post("/admin/causes/{cause_id}/hours")
async def admin_cause_add_hours(
    request: Request,
    cause_id: int,
    user: AdminDep,
    db: SessionDep,
    hours: float = Form(...),
):
    """Top a cause back up after approvals have spent its hours."""
    service = _cause_service(db)

    try:
        cause = service.add_hours(cause_id=cause_id, hours=hours)
    except ValueError as exc:
        flash(request, str(exc), "warning")
    else:
        flash(
            request,
            f"{hours:g} hours added to {cause.cause_name}.",
            "success",
        )

    return RedirectResponse(url=request.url_for("admin_causes_view"), status_code=303)
