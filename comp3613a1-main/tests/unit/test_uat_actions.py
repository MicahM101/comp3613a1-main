"""Unit tests — the actions taken in the UAT cases, one service at a time.

Derived from the UAT plan (docs/test-plans/01-user-acceptance-test-plan.md),
which is itself derived from the three workflow wireframes. Each test
exercises a single service with in-memory fake repositories — no database,
no HTTP server. The UAT case number is noted above every test so a
screenshot can be matched back to the plan.

Run:  python -m pytest tests/unit -q
"""

import io
from datetime import date

import jwt
import pytest
from starlette.datastructures import UploadFile

from app.config import get_settings
from app.models.admin import Admin
from app.models.reward import Charity, HoursRedemption, Reward
from app.models.student import Student
from app.models.submission import Submission, VolunteerCause
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.cause_service import CauseService
from app.services.review_service import ReviewService
from app.services.redeem_service import RedeemService
from app.services.submission import SubmissionService

from .fakes import (
    FakeAdminRepository,
    FakeCharityRepository,
    FakeHoursRedemptionRepository,
    FakeRewardRepository,
    FakeStudentRepository,
    FakeSubmissionRepository,
    FakeUserRepository,
    FakeVolunteerCauseRepository,
)

BOB = User(id=7, username="bob", email="bob@example.com",
           password="x", role="regular_user")
ADMIN_USER = User(id=9, username="admin", email="admin@example.com",
                  password="x", role="admin")


def turtles(hours: float = 35.0) -> VolunteerCause:
    """A fresh cause per test — decide() mutates the row in place."""
    return VolunteerCause(
        id=1, cause_name="Save the Turtles!",
        description="Clean the turtle nest.", hours_available=hours,
    )


def math_help(hours: float = 30.0) -> VolunteerCause:
    return VolunteerCause(
        id=2, cause_name="Math Help Center",
        description="Tutor struggling students.", hours_available=hours,
    )


def pending_row(submission_id: int = 1, *, cause_id: int = 1, hours: float = 5.0,
                student_id: int = 3, state: str = "pending") -> Submission:
    return Submission(
        id=submission_id, student_id=student_id, cause_id=cause_id,
        hours_completed=hours, date_completed=date(2026, 10, 1),
        start_time="09:00 AM", state=state,
        document_path="/static/uploads/abc.pdf",
        original_document_name="bob-form.pdf",
    )


def upload(name: str, content: bytes = b"%PDF-1.4 test") -> UploadFile:
    return UploadFile(file=io.BytesIO(content), filename=name)


def submission_service(causes=None, submissions=None, students=None):
    cause_repo = FakeVolunteerCauseRepository(causes)
    submission_repo = FakeSubmissionRepository(submissions, causes=causes)
    student_repo = FakeStudentRepository(students)
    return SubmissionService(submission_repo, cause_repo, student_repo)


def review_service(submissions=None, causes=None, students=None, admins=None):
    cause_repo = FakeVolunteerCauseRepository(causes)
    submission_repo = FakeSubmissionRepository(submissions, causes=causes)
    student_repo = FakeStudentRepository(students)
    admin_repo = FakeAdminRepository(admins)
    service = ReviewService(submission_repo, cause_repo, student_repo, admin_repo)
    return service, submission_repo, cause_repo, admin_repo


def bob_profile(total: float = 6.0):
    """bob's student profile plus one approved submission of `total` hours."""
    students = [Student(id=3, user_id=BOB.id, name="bob", email=BOB.email)]
    approved = [Submission(
        id=1, student_id=3, cause_id=1, hours_completed=total,
        date_completed=date(2026, 10, 1), state="approved",
    )]
    return students, approved


def redeem_service(rewards=None, redemptions=None, approved=None,
                   students=None, charities=None):
    reward_repo = FakeRewardRepository(rewards)
    charity_repo = FakeCharityRepository(charities)
    redemption_repo = FakeHoursRedemptionRepository(redemptions)
    submission_repo = FakeSubmissionRepository(
        approved, causes=[turtles(hours=10.0)]
    )
    student_repo = FakeStudentRepository(students)
    service = RedeemService(
        reward_repo, charity_repo, redemption_repo, submission_repo, student_repo
    )
    return service, redemption_repo


# --- UAT 1.1 / 1.2 / 1.3: login and register --------------------------------


def test_uat_1_3_register_stores_a_hash_and_refuses_duplicates():
    """UAT 1.3 — registering keeps the password safe and blocks reuse."""
    repo = FakeUserRepository()
    service = AuthService(repo)

    user = service.register_user("bob", "bob@example.com", "bobpass")

    assert user.username == "bob"
    assert user.password != "bobpass"              # never stored in clear text
    assert "bobpass" not in user.password
    assert repo.get_by_username("bob") is not None

    with pytest.raises(Exception, match="UNIQUE"):
        service.register_user("bob", "other@example.com", "anotherpass")


def test_uat_1_1_login_returns_a_token_with_id_and_role():
    """UAT 1.1 — a correct username/password yields the session token."""
    service = AuthService(FakeUserRepository())
    service.register_user("bob", "bob@example.com", "bobpass")

    token = service.authenticate_user("bob", "bobpass")

    payload = jwt.decode(
        token,
        get_settings().secret_key,
        algorithms=[get_settings().jwt_algorithm],
    )
    assert payload["sub"] == "1"                   # the created user's id
    assert payload["role"] == "regular_user"
    assert "exp" in payload


def test_uat_1_2_login_rejects_a_wrong_password():
    """UAT 1.2 — a wrong password grants no session."""
    service = AuthService(FakeUserRepository())
    service.register_user("bob", "bob@example.com", "bobpass")

    assert service.authenticate_user("bob", "wrongpass") is None
    assert service.authenticate_user("nobody", "bobpass") is None


# --- UAT 1.5 / 1.6 / 1.7 / 1.8: submit hours --------------------------------


def test_uat_1_5_the_form_lists_the_causes_a_student_can_serve():
    """UAT 1.5 — the cause dropdown is fed by CauseService.list_causes."""
    service = CauseService(
        FakeVolunteerCauseRepository([math_help(), turtles()])
    )

    names = [c.cause_name for c in service.list_causes()]

    assert names == ["Math Help Center", "Save the Turtles!"]   # name order


def test_uat_1_7_hours_beyond_the_cause_are_refused():
    """UAT 1.7 (hours) — valid hours fit; more than the cause offers is refused."""
    service = submission_service([turtles(hours=35.0)])

    cause = service.check_hours_fit(cause_id=1, hours=10.0)
    assert cause.cause_name == "Save the Turtles!"

    with pytest.raises(ValueError, match="exceed the total available"):
        service.check_hours_fit(cause_id=1, hours=999.0)


def test_uat_1_6_7_only_allowed_document_types_are_stored(uploads_dir):
    """UAT 1.6/1.7 (document) — PDFs are stored, .exe is refused."""
    service = submission_service([turtles()])

    path, original = service.save_document(upload("forms/bob-form.pdf"))

    assert path.startswith("/static/uploads/")
    assert original == "bob-form.pdf"              # folder part dropped
    assert (uploads_dir / path.rsplit("/", 1)[-1]).is_file()

    with pytest.raises(ValueError, match="Unsupported file type"):
        service.save_document(upload("malware.exe"))


def test_uat_1_6_a_confirmed_submission_is_recorded_as_pending():
    """UAT 1.6 — Confirm stores a pending row linked to its document."""
    students = [Student(id=3, user_id=BOB.id, name="bob", email=BOB.email)]
    service = submission_service([turtles()], students=students)

    recorded = service.record_submission(
        user=BOB,
        cause_id=1,
        hours=5.0,
        date_completed=date(2026, 10, 5),
        start_time="09:30 AM",
        document_path="/static/uploads/abc.pdf",
        original_document_name="bob-form.pdf",
    )

    assert recorded.state == "pending"             # always waits on an admin
    assert recorded.admin_id is None
    assert recorded.hours_completed == 5.0
    assert recorded.document_path == "/static/uploads/abc.pdf"
    # the Account-page tracker shows it back to the student, newest first
    rows = service.my_submissions(3)
    assert rows[0]["submission"].id == recorded.id
    assert rows[0]["submission"].state == "pending"
    # a pending row never counts towards Hours Earned
    assert service.total_hours_earned(3) == 0.0


# --- UAT 1.9 / 1.10 / 1.11 / 1.12 / 1.13: admin review ----------------------


def test_uat_1_9_the_queue_lists_only_pending_requests_and_searches():
    """UAT 1.9 — the queue shows pending rows only and honours the search box."""
    service, *_ = review_service(
        [
            pending_row(1, state="pending"),
            pending_row(2, state="approved"),
            pending_row(3, state="rejected"),
        ],
        [turtles(), math_help()],
        students=[Student(id=3, user_id=7, name="bob", email="bob@example.com")],
    )

    rows = service.queue()

    assert [r["submission"].id for r in rows] == [1]      # pending only
    assert rows[0]["cause_name"] == "Save the Turtles!"
    assert rows[0]["student"].name == "bob"

    # "Search by Student ID, Submission ID, or Cause"
    assert [r["submission"].id for r in service.queue(search="math")] == []
    assert [r["submission"].id for r in service.queue(search="turtles")] == [1]
    assert [r["submission"].id for r in service.queue(search="1")] == [1]


def test_uat_1_10_review_detail_carries_the_student_and_the_document():
    """UAT 1.10 — the review card shows who/what plus the running total."""
    service, *_ = review_service(
        [
            pending_row(1, hours=5.0),
            pending_row(2, hours=6.0, state="approved"),
        ],
        [turtles()],
        students=[Student(id=3, user_id=7, name="bob", email="bob@example.com")],
    )

    detail = service.review_detail(1)

    assert detail["student"].name == "bob"
    assert detail["cause_name"] == "Save the Turtles!"
    assert detail["submission"].document_path == "/static/uploads/abc.pdf"
    assert detail["submission"].original_document_name == "bob-form.pdf"
    assert detail["total_hours"] == 6.0            # approved only, computed live


def test_uat_1_11_approving_records_the_admin_and_spends_cause_hours():
    """UAT 1.11 — approval sets status, names the admin, spends the cause."""
    service, _, causes, admins = review_service(
        [pending_row(hours=5.0)], [turtles(hours=35.0)]
    )

    decided = service.decide(submission_id=1, user=ADMIN_USER, state="approved")

    assert decided.state == "approved"
    assert decided.admin_id is not None            # "which admin verified it"
    assert causes.get_by_id(1).hours_available == 30.0   # 35 - 5
    assert len(admins.admins) == 1                 # the admin profile exists


def test_uat_1_12_rejecting_leaves_the_cause_balance_alone():
    """UAT 1.12 — rejection changes the status but spends nothing."""
    service, _, causes, _ = review_service(
        [pending_row(hours=5.0)], [turtles(hours=35.0)]
    )

    decided = service.decide(submission_id=1, user=ADMIN_USER, state="rejected")

    assert decided.state == "rejected"
    assert causes.get_by_id(1).hours_available == 35.0    # untouched


def test_uat_1_13_a_decided_submission_cannot_be_decided_again():
    """UAT 1.13 — a second decision is refused, nothing double-counted."""
    service, submissions, _, _ = review_service(
        [pending_row(state="approved")], [turtles(hours=35.0)]
    )

    with pytest.raises(ValueError, match="already been reviewed"):
        service.decide(submission_id=1, user=ADMIN_USER, state="rejected")

    assert submissions.get_by_id(1).state == "approved"   # unchanged
    assert submissions.get_by_id(1).admin_id is None


# --- UAT 1.14 / 1.15 / 1.16 / 1.17 / 1.18: redeem progress ------------------


def test_uat_1_14_the_grid_flags_affordable_and_unaffordable_rewards():
    """UAT 1.14 — Total Hours and the affordable/unaffordable flags per card."""
    WAIVER = Reward(id=1, reward_name="Library Late-Fee Waiver", hour_cost=5.0)
    GYM = Reward(id=2, reward_name="Gym Day Pass", hour_cost=8.0)
    students, approved = bob_profile(total=6.0)
    service, _ = redeem_service(
        rewards=[WAIVER, GYM], approved=approved, students=students
    )

    rows = service.grid(BOB)

    assert rows["total"] == 6.0                     # "Total Hours: 6"
    by_name = {r["reward"].reward_name: r for r in rows["rewards"]}
    assert by_name["Library Late-Fee Waiver"]["affordable"] is True
    assert by_name["Library Late-Fee Waiver"]["needs"] == 0.0
    assert by_name["Gym Day Pass"]["affordable"] is False
    assert by_name["Gym Day Pass"]["needs"] == 2.0  # 8 - 6


def test_uat_1_15_16_redeeming_spends_hours_and_unaffordable_is_refused():
    """UAT 1.15/1.16 — an affordable reward is spent; a too-pricey one refused."""
    WAIVER = Reward(id=1, reward_name="Library Late-Fee Waiver", hour_cost=5.0)
    GYM = Reward(id=2, reward_name="Gym Day Pass", hour_cost=8.0)
    students, approved = bob_profile(total=6.0)
    service, redemption_repo = redeem_service(
        rewards=[WAIVER, GYM], approved=approved, students=students
    )

    redemption = service.redeem(user=BOB, reward_id=1)

    assert redemption.hours_spent == 5.0            # the reward's hour cost
    assert redemption.student_id == 3
    assert redemption.charity_id is None           # not a donation
    assert len(redemption_repo.redemptions) == 1
    assert service.available_hours(BOB) == 1.0     # 6 - 5 ("Total Hours: 1")

    # UAT 1.16 — the Gym Day Pass costs 8; bob has 1 left (6 at grid time)
    with pytest.raises(ValueError, match="need 7 more hours"):
        service.start(2, BOB)


def test_uat_1_17_18_charity_conversion_records_hours_and_refuses_bad_input():
    """UAT 1.17/1.18 — donations keep their partner; bad input is refused."""
    CHARITY = Reward(id=3, reward_name="Charity Conversion", hour_cost=1.0,
                     rate_note="1hr = $1")
    RED_CROSS = Charity(id=1, charity_name="Red Cross")
    students, approved = bob_profile(total=6.0)
    service, redemption_repo = redeem_service(
        rewards=[CHARITY], charities=[RED_CROSS],
        approved=approved, students=students,
    )

    # UAT 1.18 — every invalid input raises and writes nothing
    with pytest.raises(ValueError, match="how many hours"):
        service.confirm(reward_id=3, user=BOB, hours=None, charity_id=1)
    with pytest.raises(ValueError, match="more than zero"):
        service.confirm(reward_id=3, user=BOB, hours=0, charity_id=1)
    with pytest.raises(ValueError, match="partner charity"):
        service.confirm(reward_id=3, user=BOB, hours=2.0, charity_id=None)
    with pytest.raises(ValueError, match="only have 6 hours"):
        service.confirm(reward_id=3, user=BOB, hours=10.0, charity_id=1)
    assert redemption_repo.redemptions == []

    # UAT 1.17 — a valid conversion is recorded with its partner charity
    redemption = service.redeem(user=BOB, reward_id=3, hours=2.0, charity_id=1)

    assert redemption.hours_spent == 2.0
    assert redemption.charity_id == 1              # "Red Cross"
    assert service.available_hours(BOB) == 4.0     # 6 - 2
