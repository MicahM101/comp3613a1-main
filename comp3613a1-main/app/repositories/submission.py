from typing import Optional

from sqlmodel import Session, or_, select

from app.models.student import Student
from app.models.submission import Submission, VolunteerCause


class StudentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_user_id(self, user_id: int) -> Optional[Student]:
        return self.session.exec(select(Student).where(Student.user_id == user_id)).first()

    def get_by_id(self, student_id: int) -> Optional[Student]:
        return self.session.get(Student, student_id)

    def create(self, student: Student) -> Student:
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        return student


class VolunteerCauseRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self, search: str = "") -> list[VolunteerCause]:
        """Every cause, optionally narrowed by name or description."""
        term = search.strip()
        statement = select(VolunteerCause).order_by(VolunteerCause.cause_name)
        if term:
            statement = statement.where(
                or_(
                    VolunteerCause.cause_name.ilike(f"%{term}%"),
                    VolunteerCause.description.ilike(f"%{term}%"),
                )
            )
        return self.session.exec(statement).all()

    def get_by_id(self, cause_id: int) -> Optional[VolunteerCause]:
        return self.session.get(VolunteerCause, cause_id)

    def adjust_hours(self, cause_id: int, delta: float) -> Optional[VolunteerCause]:
        """Move a cause's remaining hours by ``delta`` (negative spends them).

        A cause never shows below zero — approvals that would overrun it stop
        the balance at 0 rather than going into debt.
        """
        cause = self.session.get(VolunteerCause, cause_id)
        if cause is None:
            return None
        cause.hours_available = max((cause.hours_available or 0.0) + delta, 0.0)
        self.session.add(cause)
        self.session.commit()
        self.session.refresh(cause)
        return cause


class SubmissionRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, submission: Submission) -> Submission:
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(submission)
        return submission

    def approved_by_student(self, student_id: int) -> list[Submission]:
        """Only approved hours count toward what a student has earned."""
        return self.session.exec(
            select(Submission).where(
                Submission.student_id == student_id,
                Submission.state == "approved",
            )
        ).all()

    def by_student(self, student_id: int) -> list[Submission]:
        """TODO(student): complete this method.

        Return every submission this student has made, newest first —
        regardless of its state. The tracker shows pending, approved and
        rejected alike.
        """
        return self.session.exec(
            select(Submission).where(
                Submission.student_id == student_id
            ).order_by(Submission.id.desc())
        ).all()

    def all_recent(self) -> list[Submission]:
        """Newest first — the queue Workflow 2 reviews."""
        return self.session.exec(select(Submission).order_by(Submission.id.desc())).all()

    def get_by_id(self, submission_id: int) -> Optional[Submission]:
        return self.session.get(Submission, submission_id)

    def pending_queue(self, search: str = "") -> list[Submission]:
        """The admin's review queue: pending only, newest first.

        Filtering runs here (student's choice) — one query across the joined
        cause name plus the numeric ids, so the database does the work.
        """
        term = search.strip()
        statement = (
            select(Submission)
            .join(VolunteerCause)
            .where(Submission.state == "pending")
            .order_by(Submission.id.desc())
        )

        if term:
            conditions = [VolunteerCause.cause_name.ilike(f"%{term}%")]
            if term.isdigit():
                number = int(term)
                conditions.append(Submission.student_id == number)
                conditions.append(Submission.id == number)
            statement = statement.where(or_(*conditions))

        return self.session.exec(statement).all()

    def decide(self, submission_id: int, admin_id: int, state: str) -> Optional[Submission]:
        """Record the reviewing admin and the new state."""
        submission = self.session.get(Submission, submission_id)
        if submission is None:
            return None
        submission.admin_id = admin_id
        submission.state = state
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(submission)
        return submission
