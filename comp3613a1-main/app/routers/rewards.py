from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from . import router, templates


@router.get("/rewards", response_class=HTMLResponse)
async def rewards_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    """Placeholder until Workflow 3 (RedeemProgress) is built."""
    return templates.TemplateResponse(
        request=request,
        name="rewards.html",
        context={"user": user},
    )
