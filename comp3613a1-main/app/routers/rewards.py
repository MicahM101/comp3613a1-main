from fastapi import Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.reward import (
    CharityRepository,
    HoursRedemptionRepository,
    RewardRepository,
)
from app.repositories.submission import StudentRepository, SubmissionRepository
from app.services.redeem_service import RedeemService
from app.utilities.flash import flash

from . import router, templates


def _redeem_service(db: SessionDep) -> RedeemService:
    return RedeemService(
        RewardRepository(db),
        CharityRepository(db),
        HoursRedemptionRepository(db),
        SubmissionRepository(db),
        StudentRepository(db),
    )


@router.get("/rewards", response_class=HTMLResponse)
async def rewards_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    q: str = Query(""),
):
    """Workflow 3 — the rewards grid and the student's running total."""
    service = _redeem_service(db)

    return templates.TemplateResponse(
        request=request,
        name="rewards.html",
        context={"user": user, **service.grid(user, search=q)},
    )


@router.get("/rewards/{reward_id}/redeem", response_class=HTMLResponse)
async def reward_redeem_start(
    request: Request,
    reward_id: int,
    user: AuthDep,
    db: SessionDep,
):
    """Select → the charity screen, or straight to confirmation (Phase 4)."""
    service = _redeem_service(db)

    try:
        detail = service.start(reward_id, user)
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(url=request.url_for("rewards_view"), status_code=303)

    if detail is None:
        raise HTTPException(status_code=404, detail="Reward not found")

    if detail["is_charity"]:
        return templates.TemplateResponse(
            request=request,
            name="redeem_charity.html",
            context={"user": user, **detail},
        )

    return templates.TemplateResponse(
        request=request,
        name="redeem_confirm.html",
        context={
            "user": user,
            "reward": detail["reward"],
            "hours": detail["reward"].hour_cost,
            "charity": None,
            "total": detail["total"],
            "is_charity": False,
        },
    )


@router.get("/rewards/{reward_id}/confirm", response_class=HTMLResponse)
async def reward_confirm_view(
    request: Request,
    reward_id: int,
    user: AuthDep,
    db: SessionDep,
    hours: float | None = Query(None),
    charity_id: int | None = Query(None),
):
    """The 'Are you sure?' screen after the charity hours are chosen."""
    service = _redeem_service(db)

    try:
        quote = service.confirm(
            reward_id=reward_id,
            user=user,
            hours=hours,
            charity_id=charity_id,
        )
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(url=request.url_for("rewards_view"), status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="redeem_confirm.html",
        context={
            "user": user,
            **quote,
            "is_charity": quote["charity"] is not None,
        },
    )


@router.post("/rewards/{reward_id}/redeem")
async def reward_redeem_apply(
    request: Request,
    reward_id: int,
    user: AuthDep,
    db: SessionDep,
    hours: float | None = Form(None),
    charity_id: int | None = Form(None),
):
    """Record a confirmed redemption and send the student back to the grid.

    The service owns every check (unknown reward, not enough hours, missing
    charity) — it raises ValueError for those, so catch it and flash the
    message instead of letting the request fail.
    """
    service = _redeem_service(db)

    try:
        service.redeem(
            reward_id=reward_id,
            user=user,
            hours=hours,
            charity_id=charity_id,
        )
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(url=request.url_for("rewards_view"), status_code=303)

    flash(request, "Redemption successful!", "success")
    return RedirectResponse(url=request.url_for("rewards_view"), status_code=303)

