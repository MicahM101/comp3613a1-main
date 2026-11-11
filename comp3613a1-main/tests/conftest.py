"""Shared pytest fixtures for COMP 3613 Assignment 2.

The app builds its SQLAlchemy engine from ``DATABASE_URI`` at import time,
so the test database must be chosen *before* any ``app.*`` module is
imported — that is why the environment is set at the top of this file.

Run from the repository root:

    python -m pytest                 # unit + integration
    python -m pytest tests/unit      # unit tests only
    python -m pytest tests/integration
"""

import os
import tempfile
from pathlib import Path

# --- environment, before any app import -------------------------------------
_TEST_DB = Path(tempfile.mkdtemp(prefix="comp3613-a2-tests-")) / "test.db"
os.environ["DATABASE_URI"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["ENV"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

# Demo credentials used across the suite (same names as `manage.py seed`).
CREDENTIALS = {
    "bob": "bobpass",      # student
    "carol": "carolpass",  # student
    "admin": "adminpass",  # admin
}


def make_client() -> TestClient:
    """A fresh TestClient (own cookie jar) against the seeded test database."""
    from app.main import app

    return TestClient(app)


def login(client: TestClient, username: str, password: str | None = None):
    """POST /login without following the redirect — the cookie is the result."""
    response = client.post(
        "/login",
        data={"username": username, "password": password or CREDENTIALS[username]},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.text
    return response


def _hash_once(password: str) -> str:
    """Hash each demo password once per run (argon2 is deliberately slow)."""
    from app.utilities.security import encrypt_password

    if password not in _PASSWORD_HASHES:
        _PASSWORD_HASHES[password] = encrypt_password(password)
    return _PASSWORD_HASHES[password]


_PASSWORD_HASHES: dict[str, str] = {}


def seed_database() -> dict:
    """Insert demo users, profiles, causes, rewards, charities and submissions.

    Mirrors the shape of `manage.py init --seed` on a smaller scale:

    - bob   — 6 approved hours (Movie Night 12h and Gym Day 8h are out of
              reach; Library Waiver 5h and Charity Conversion 1h are not),
              1 pending submission for the admin queue.
    - carol — 1 pending + 1 rejected submission (queue filtering).
    - admin — reviews the queue and tops up causes.
    """
    from datetime import date

    from app.database import engine
    from app.models.admin import Admin
    from app.models.reward import Charity, Reward
    from app.models.student import Student
    from app.models.submission import Submission, VolunteerCause
    from app.repositories.user import UserRepository
    from app.schemas.user import AdminCreate, RegularUserCreate

    with Session(engine) as session:
        users = UserRepository(session)
        bob = users.create(
            RegularUserCreate(
                username="bob", email="bob@example.com",
                password=_hash_once("bobpass"),
            )
        )
        carol = users.create(
            RegularUserCreate(
                username="carol", email="carol@example.com",
                password=_hash_once("carolpass"),
            )
        )
        admin = users.create(
            AdminCreate(
                username="admin", email="admin@example.com",
                password=_hash_once("adminpass"),
            )
        )

        session.add(Student(user_id=bob.id, name="bob", email=bob.email))
        session.add(Student(user_id=carol.id, name="carol", email=carol.email))
        session.add(Admin(user_id=admin.id, name="admin", email=admin.email))

        turtles = VolunteerCause(
            cause_name="Save the Turtles!",
            description="Help the beach club clean the turtle nest.",
            hours_available=35.0,
        )
        math_help = VolunteerCause(
            cause_name="Math Help Center",
            description="Tutor students who are struggling.",
            hours_available=30.0,
        )
        session.add(turtles)
        session.add(math_help)

        waiver = Reward(reward_name="Library Late-Fee Waiver", hour_cost=5.0)
        gym = Reward(reward_name="Gym Day Pass", hour_cost=8.0)
        movie = Reward(reward_name="Movie Night Ticket", hour_cost=12.0)
        charity_conversion = Reward(
            reward_name="Charity Conversion", hour_cost=1.0, rate_note="1hr = $1"
        )
        for reward in (waiver, gym, movie, charity_conversion):
            session.add(reward)

        red_cross = Charity(charity_name="Red Cross")
        session.add(red_cross)

        # Assign the auto-increment ids before the submissions below read them.
        session.flush()

        # bob: 6 approved hours + 1 pending row; carol: pending + rejected.
        approved = Submission(
            student_id=1, cause_id=None, hours_completed=6.0,
            date_completed=date(2026, 10, 1), start_time="09:00 AM",
            document_path="/static/uploads/seed-bob-form.pdf",
            original_document_name="bob-form.pdf", state="approved",
        )
        pending_bob = Submission(
            student_id=1, cause_id=None, hours_completed=3.0,
            date_completed=date(2026, 10, 5), start_time="02:30 PM",
            document_path="/static/uploads/seed-bob-pending.pdf",
            original_document_name="bob-pending.pdf", state="pending",
        )
        pending_carol = Submission(
            student_id=2, cause_id=None, hours_completed=4.0,
            date_completed=date(2026, 10, 6), start_time="08:45 AM",
            document_path="/static/uploads/seed-carol-pending.pdf",
            original_document_name="carol-pending.pdf", state="pending",
        )
        rejected_carol = Submission(
            student_id=2, cause_id=None, hours_completed=2.0,
            date_completed=date(2026, 9, 30), start_time="04:00 PM",
            state="rejected",
        )
        # student_id / cause_id are set after the rows above exist (ids 1..2).
        for submission, cause in (
            (approved, turtles),
            (pending_bob, math_help),
            (pending_carol, turtles),
            (rejected_carol, math_help),
        ):
            submission.cause_id = cause.id
            session.add(submission)

        session.commit()

        return {
            "users": {"bob": bob.id, "carol": carol.id, "admin": admin.id},
            "causes": {"turtles": turtles.id, "math_help": math_help.id},
            "rewards": {
                "waiver": waiver.id,
                "gym": gym.id,
                "movie": movie.id,
                "charity_conversion": charity_conversion.id,
            },
            "charities": {"red_cross": red_cross.id},
            "submissions": {
                "approved": approved.id,
                "pending_bob": pending_bob.id,
                "pending_carol": pending_carol.id,
                "rejected_carol": rejected_carol.id,
            },
        }


# --- fixtures ----------------------------------------------------------------


@pytest.fixture()
def db():
    """A clean schema for one test (the app engine points at a temp SQLite)."""
    from app.database import create_db_and_tables, drop_all, engine

    engine.echo = False  # keep pytest output readable
    drop_all()
    create_db_and_tables()
    yield engine
    drop_all()


@pytest.fixture()
def seed(db):
    """Demo rows for one test; ids keyed by name."""
    return seed_database()


@pytest.fixture()
def query(db):
    """Run a short-lived read/write against the test database."""

    def _run(callback):
        from app.database import engine

        with Session(engine) as session:
            return callback(session)

    return _run


@pytest.fixture()
def client(db):
    """Unauthenticated client (cookies are added by the login fixtures)."""
    with make_client() as test_client:
        yield test_client


@pytest.fixture()
def student_client(seed):
    """Client with bob (the student) signed in."""
    with make_client() as test_client:
        login(test_client, "bob")
        yield test_client


@pytest.fixture()
def admin_client(seed):
    """Client with the admin signed in."""
    with make_client() as test_client:
        login(test_client, "admin")
        yield test_client


@pytest.fixture()
def uploads_dir(tmp_path, monkeypatch):
    """Keep test uploads out of the real ``app/static/uploads`` folder."""
    import app.services.submission as submission_module

    target = tmp_path / "uploads"
    target.mkdir()
    monkeypatch.setattr(submission_module, "UPLOAD_DIR", target)
    return target
