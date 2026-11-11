"""Read-only JSON API (`/api/...`) — REST mirrors of the main workflows.

Routes stay thin: bind the request, call a service, shape the response.
No SQL lives here (see `docs/diagrams/application-components.jpg`).
"""

from fastapi import Query

from app.dependencies.auth import AdminDep, AuthDep
from app.dependencies.session import SessionDep
from app.repositories.admin import AdminRepository
from app.repositories.reward import (
    CharityRepository,
    HoursRedemptionRepository,
    RewardRepository,
)
from app.repositories.submission import (
    StudentRepository,
    SubmissionRepository,
    VolunteerCauseRepository,
)
from app.schemas import CauseResponse, RewardResponse, SubmissionResponse
from app.services.cause_service import CauseService
from app.services.redeem_service import RedeemService
from app.services.review_service import ReviewService

from . import api_router


def _cause_service(db: SessionDep) -> CauseService:
    return CauseService(VolunteerCauseRepository(db))


def _redeem_service(db: SessionDep) -> RedeemService:
    return RedeemService(
        RewardRepository(db),
        CharityRepository(db),
        HoursRedemptionRepository(db),
        SubmissionRepository(db),
        StudentRepository(db),
    )


def _review_service(db: SessionDep) -> ReviewService:
    return ReviewService(
        SubmissionRepository(db),
        VolunteerCauseRepository(db),
        StudentRepository(db),
        AdminRepository(db),
    )


@api_router.get("/causes", response_model=list[CauseResponse], name="api_list_causes")
async def list_causes(db: SessionDep, user: AuthDep):
    """Every cause a student can serve — JSON mirror of the Causes page."""
    return _cause_service(db).list_causes()


@api_router.get("/rewards", response_model=list[RewardResponse], name="api_list_rewards")
async def list_rewards(
    db: SessionDep,
    user: AuthDep,
    q: str = Query(""),
):
    """The rewards grid for the signed-in student, affordability included."""
    grid = _redeem_service(db).grid(user, search=q)
    return [
        RewardResponse(
            id=row["reward"].id,
            reward_name=row["reward"].reward_name,
            hour_cost=row["reward"].hour_cost,
            rate_note=row["reward"].rate_note,
            affordable=row["affordable"],
            hours_needed=row["needs"],
        )
        for row in grid["rewards"]
    ]


@api_router.get(
    "/submissions", response_model=list[SubmissionResponse], name="api_list_submissions"
)
async def list_submissions(
    db: SessionDep,
    user: AdminDep,
    q: str = Query(""),
):
    """The admin's review queue — JSON mirror of the Submissions page."""
    rows = _review_service(db).queue(search=q)
    return [
        SubmissionResponse(
            id=row["submission"].id,
            student_id=row["submission"].student_id,
            student_name=row["student"].name if row["student"] else None,
            cause_id=row["submission"].cause_id,
            cause_name=row["cause_name"],
            hours_completed=row["submission"].hours_completed,
            date_completed=row["submission"].date_completed,
            start_time=row["submission"].start_time,
            state=row["submission"].state,
            document_path=row["submission"].document_path,
            original_document_name=row["submission"].original_document_name,
        )
        for row in rows
    ]
