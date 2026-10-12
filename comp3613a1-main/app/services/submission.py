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

    def save_document(self, document: UploadFile) -> str:
        """Store the uploaded form and return its public path."""
        suffix = Path(document.filename or "document").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type '{suffix}'.")
        stored_name = f"{uuid.uuid4().hex}{suffix}"
        target = UPLOAD_DIR / stored_name
        with target.open("wb") as handle:
            handle.write(document.file.read())
        return f"/static/uploads/{stored_name}"

    def record_submission(
        self,
        *,
        user: User,
        cause_id: int,
        hours: float,
        date_completed,
        start_time: str,
        document_path: str,
    ) -> Submission:
        """A new submission always starts life waiting on an admin."""
        student = self.get_student_for(user)
        submission = Submission(
            student_id=student.id,
            admin_id=None,
            cause_id=cause_id,
            hours_completed=hours,
            date_completed=date_completed,
            start_time=start_time,
            document_path=document_path,
            state="pending",
        )
        return self.submissions.add(submission)
