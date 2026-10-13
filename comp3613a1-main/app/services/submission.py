import uuid
from pathlib import Path

from fastapi import UploadFile

from app.models.submission import Submission, VolunteerCause
from app.models.user import User
from app.repositories.submission import (
    StudentRepository,
    SubmissionRepository,
    VolunteerCauseRepository,
)

# Kept simple on purpose (student's choice): uploads live under static/ and are
# read back through the same URL.
UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx"}


class SubmissionService:
    def __init__(
        self,
        submissions: SubmissionRepository,
        causes: VolunteerCauseRepository,
        students: StudentRepository,
    ):
        self.submissions = submissions
        self.causes = causes
        self.students = students

    def get_student_for(self, user: User):
        """The student profile behind a login (created on first use)."""
        student = self.students.get_by_user_id(user.id)
        if student is None:
            from app.models.student import Student

            student = self.students.create(
                Student(user_id=user.id, name=user.username, email=user.email)
            )
        return student

    def list_causes(self) -> list[VolunteerCause]:
        return self.causes.list_all()

    def recent_contributions(self, student_id: int) -> list[dict]:
        """Cause cards: one per cause the student has approved hours for."""
        approved = self.submissions.approved_by_student(student_id)
        by_cause: dict[int, dict] = {}
        for submission in approved:
            cause = self.causes.get_by_id(submission.cause_id)
            if cause is None:
                continue
            entry = by_cause.setdefault(
                cause.id,
                {"cause": cause, "hours_earned": 0.0},
            )
            entry["hours_earned"] += submission.hours_completed or 0.0
        return list(by_cause.values())

    def total_hours_earned(self, student_id: int) -> float:
        return sum(s.hours_completed or 0.0 for s in self.submissions.approved_by_student(student_id))

    def my_submissions(self, student_id: int) -> list[dict]:
        """The student's own tracker rows — every state, newest first."""
        rows = []
        for submission in self.submissions.by_student(student_id):
            cause = self.causes.get_by_id(submission.cause_id)
            rows.append(
                {
                    "submission": submission,
                    "cause_name": cause.cause_name if cause else "—",
                }
            )
        return rows

    def save_document(self, document: UploadFile) -> tuple[str, str]:
        """Store the upload; return (public path, original file name)."""
        suffix = Path(document.filename or "document").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type '{suffix}'.")
        stored_name = f"{uuid.uuid4().hex}{suffix}"
        target = UPLOAD_DIR / stored_name
        with target.open("wb") as handle:
            handle.write(document.file.read())
        return f"/static/uploads/{stored_name}", Path(document.filename).name

    def check_hours_fit(self, *, cause_id: int, hours: float) -> VolunteerCause:
        """A submission cannot claim more hours than the cause still offers.

        Approvals are what actually spend a cause's hours (ReviewService.decide),
        so this checks the balance as it stands now — the same number the
        Causes page shows the student.
        """
        cause = self.causes.get_by_id(cause_id)
        if cause is None:
            raise ValueError("That cause no longer exists.")

        available = cause.hours_available or 0.0
        if hours > available:
            raise ValueError(
                "Your hours exceed the total available for this cause — "
                f"{cause.cause_name} has {available:g} hours."
            )
        return cause

    def record_submission(
        self,
        *,
        user: User,
        cause_id: int,
        hours: float,
        date_completed,
        start_time: str,
        document_path: str,
        original_document_name: str | None = None,
    ) -> Submission:
        """A new submission always starts life waiting on an admin."""
        self.check_hours_fit(cause_id=cause_id, hours=hours)
        student = self.get_student_for(user)
        submission = Submission(
            student_id=student.id,
            admin_id=None,
            cause_id=cause_id,
            hours_completed=hours,
            date_completed=date_completed,
            start_time=start_time,
            document_path=document_path,
            original_document_name=original_document_name,
            state="pending",
        )
        return self.submissions.add(submission)
