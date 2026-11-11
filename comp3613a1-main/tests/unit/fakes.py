"""In-memory stand-ins for the repositories.

Unit tests exercise one service at a time, so these fakes replace the
database layer completely — no engine, no session, no SQL. Each fake mirrors
the signature and ordering of the real repository it replaces.
"""

from __future__ import annotations

from typing import Optional

from app.models.admin import Admin
from app.models.reward import Charity, HoursRedemption, Reward
from app.models.student import Student
from app.models.submission import Submission, VolunteerCause
from app.models.user import User


class _InMemory:
    """Auto-incrementing id helper shared by the fakes."""

    def __init__(self):
        self._next_id = 1

    def _assign_id(self, row):
        if getattr(row, "id", None) is None:
            row.id = self._next_id
        self._next_id = max(self._next_id, row.id + 1)
        return row


class FakeVolunteerCauseRepository(_InMemory):
    def __init__(self, causes: list[VolunteerCause] | None = None):
        super().__init__()
        # Shared list, so mutations are visible to the other fakes.
        self.causes = causes if causes is not None else []

    def list_all(self, search: str = "") -> list[VolunteerCause]:
        term = search.strip().lower()
        rows = [
            cause
            for cause in self.causes
            if not term
            or term in cause.cause_name.lower()
            or term in (cause.description or "").lower()
        ]
        return sorted(rows, key=lambda cause: cause.cause_name)

    def get_by_id(self, cause_id: int) -> Optional[VolunteerCause]:
        return next((c for c in self.causes if c.id == cause_id), None)

    def adjust_hours(self, cause_id: int, delta: float) -> Optional[VolunteerCause]:
        cause = self.get_by_id(cause_id)
        if cause is None:
            return None
        cause.hours_available = max((cause.hours_available or 0.0) + delta, 0.0)
        return cause


class FakeSubmissionRepository(_InMemory):
    def __init__(
        self,
        submissions: list[Submission] | None = None,
        causes: list[VolunteerCause] | None = None,
    ):
        super().__init__()
        self.submissions = submissions if submissions is not None else []
        self.causes = causes if causes is not None else []

    def add(self, submission: Submission) -> Submission:
        if submission not in self.submissions:
            self.submissions.append(submission)
        return self._assign_id(submission)

    def approved_by_student(self, student_id: int) -> list[Submission]:
        return [
            s
            for s in self.submissions
            if s.student_id == student_id and s.state == "approved"
        ]

    def by_student(self, student_id: int) -> list[Submission]:
        rows = [s for s in self.submissions if s.student_id == student_id]
        return sorted(rows, key=lambda s: s.id or 0, reverse=True)

    def all_recent(self) -> list[Submission]:
        return sorted(self.submissions, key=lambda s: s.id or 0, reverse=True)

    def get_by_id(self, submission_id: int) -> Optional[Submission]:
        return next((s for s in self.submissions if s.id == submission_id), None)

    def pending_queue(self, search: str = "") -> list[Submission]:
        term = search.strip()
        rows = [s for s in self.submissions if s.state == "pending"]
        if term:
            def matches(submission: Submission) -> bool:
                cause = next(
                    (c for c in self.causes if c.id == submission.cause_id), None
                )
                name = cause.cause_name if cause else ""
                if term.lower() in name.lower():
                    return True
                if term.isdigit():
                    number = int(term)
                    return (
                        submission.student_id == number or submission.id == number
                    )
                return False

            rows = [s for s in rows if matches(s)]
        return sorted(rows, key=lambda s: s.id or 0, reverse=True)

    def decide(
        self, submission_id: int, admin_id: int, state: str
    ) -> Optional[Submission]:
        submission = self.get_by_id(submission_id)
        if submission is None:
            return None
        submission.admin_id = admin_id
        submission.state = state
        return submission


class FakeStudentRepository(_InMemory):
    def __init__(self, students: list[Student] | None = None):
        super().__init__()
        self.students = students if students is not None else []

    def get_by_user_id(self, user_id: int) -> Optional[Student]:
        return next((s for s in self.students if s.user_id == user_id), None)

    def get_by_id(self, student_id: int) -> Optional[Student]:
        return next((s for s in self.students if s.id == student_id), None)

    def create(self, student: Student) -> Student:
        self.students.append(student)
        return self._assign_id(student)


class FakeAdminRepository(_InMemory):
    def __init__(self, admins: list[Admin] | None = None):
        super().__init__()
        self.admins = admins if admins is not None else []

    def get_by_user_id(self, user_id: int) -> Optional[Admin]:
        return next((a for a in self.admins if a.user_id == user_id), None)

    def get_by_id(self, admin_id: int) -> Optional[Admin]:
        return next((a for a in self.admins if a.id == admin_id), None)

    def create(self, admin: Admin) -> Admin:
        self.admins.append(admin)
        return self._assign_id(admin)


class FakeRewardRepository(_InMemory):
    def __init__(self, rewards: list[Reward] | None = None):
        super().__init__()
        self.rewards = rewards if rewards is not None else []

    def list_all(self, search: str = "") -> list[Reward]:
        term = search.strip().lower()
        rows = [
            r for r in self.rewards if not term or term in r.reward_name.lower()
        ]
        return sorted(rows, key=lambda r: r.hour_cost)

    def get_by_id(self, reward_id: int) -> Optional[Reward]:
        return next((r for r in self.rewards if r.id == reward_id), None)


class FakeCharityRepository(_InMemory):
    def __init__(self, charities: list[Charity] | None = None):
        super().__init__()
        self.charities = charities if charities is not None else []

    def list_all(self) -> list[Charity]:
        return sorted(self.charities, key=lambda c: c.charity_name)

    def get_by_id(self, charity_id: int) -> Optional[Charity]:
        return next((c for c in self.charities if c.id == charity_id), None)


class FakeHoursRedemptionRepository(_InMemory):
    def __init__(self, redemptions: list[HoursRedemption] | None = None):
        super().__init__()
        self.redemptions = redemptions if redemptions is not None else []

    def add(self, redemption: HoursRedemption) -> HoursRedemption:
        self.redemptions.append(redemption)
        return self._assign_id(redemption)

    def by_student(self, student_id: int) -> list[HoursRedemption]:
        return [r for r in self.redemptions if r.student_id == student_id]

    def total_spent(self, student_id: int) -> float:
        return sum(r.hours_spent or 0.0 for r in self.by_student(student_id))


class FakeUserRepository(_InMemory):
    """Mirrors UserRepository.create's duplicate behaviour (it re-raises)."""

    def __init__(self, users: list[User] | None = None):
        super().__init__()
        self.users = users if users is not None else []

    def create(self, user_data) -> User:
        if any(u.username == user_data.username for u in self.users):
            raise Exception("UNIQUE constraint failed: user.username")
        if any(u.email == user_data.email for u in self.users):
            raise Exception("UNIQUE constraint failed: user.email")
        user = User.model_validate(user_data)
        self.users.append(user)
        return self._assign_id(user)

    def get_by_username(self, username: str) -> Optional[User]:
        return next((u for u in self.users if u.username == username), None)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return next((u for u in self.users if u.id == user_id), None)

    def get_all_users(self) -> list[User]:
        return list(self.users)
