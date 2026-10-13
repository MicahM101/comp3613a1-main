from app.models.admin import Admin
from app.models.submission import Submission
from app.models.user import User
from app.repositories.admin import AdminRepository
from app.repositories.submission import (
    StudentRepository,
    SubmissionRepository,
    VolunteerCauseRepository,
)

# The three states a submission can be in, per the ERD note on `state`.
DECISIONS = {"approved": "approved", "rejected": "rejected"}


class ReviewService:
    """Workflow 2 — VerifyHours: the queue, the review card, the decision."""

    def __init__(
        self,
        submissions: SubmissionRepository,
        causes: VolunteerCauseRepository,
        students: StudentRepository,
        admins: AdminRepository,
    ):
        self.submissions = submissions
        self.causes = causes
        self.students = students
        self.admins = admins

    def get_admin_for(self, user: User) -> Admin:
        """The Admin profile behind a login (created on first review).

        Student's choice: keep separate Admin rows and store ``admin.id`` on
        the submission, so the ERD's "which admin verified it" holds.
        """
        admin = self.admins.get_by_user_id(user.id)
        if admin is None:
            admin = self.admins.create(
                Admin(user_id=user.id, name=user.username, email=user.email)
            )
        return admin

    def queue(self, search: str = "") -> list[dict]:
        """Pending submissions for the admin, with the names the table shows."""
        rows = []
        for submission in self.submissions.pending_queue(search):
            rows.append(self._decorate(submission))
        return rows

    def review_detail(self, submission_id: int) -> dict | None:
        """Everything the review card and the confirmation dialog need."""
        submission = self.submissions.get_by_id(submission_id)
        if submission is None:
            return None
        detail = self._decorate(submission)
        student = self.students.get_by_id(submission.student_id)
        detail["student"] = student
        # Phase 4 note: the admin sees the student's running total, computed
        # from approved hours — never stored on the submission.
        detail["total_hours"] = self.total_hours_for(submission.student_id)
        return detail

    def decide(self, *, submission_id: int, user: User, state: str) -> Submission:
        """Approve or reject, recording which admin did it."""
        if state not in DECISIONS:
            raise ValueError("Unknown decision.")

        submission = self.submissions.get_by_id(submission_id)
        if submission is None:
            raise ValueError("That submission no longer exists.")
        if submission.state != "pending":
            raise ValueError("This submission has already been reviewed.")

        # Student's rule: a cause must still have the hours for an approval
        # to go through. Short of them, refuse before anything is written —
        # the admin tops the cause up on the Causes page and tries again.
        hours = submission.hours_completed or 0.0
        if DECISIONS[state] == "approved":
            cause = self.causes.get_by_id(submission.cause_id)
            if cause is not None:
                remaining = cause.hours_available or 0.0
                if remaining < hours:
                    raise ValueError(
                        f"{cause.cause_name} only has {remaining:g} hours left "
                        f"and this approval needs {hours:g}. Add hours on the "
                        "Causes page first."
                    )

        admin = self.get_admin_for(user)
        decided = self.submissions.decide(submission_id, admin.id, DECISIONS[state])

        # Approved hours come out of what the cause still has to give.
        # Rejections and pending rows leave the cause's balance alone.
        if decided is not None and decided.state == "approved":
            self.causes.adjust_hours(decided.cause_id, -(decided.hours_completed or 0.0))

        return decided

    def total_hours_for(self, student_id: int) -> float:
        return sum(
            s.hours_completed or 0.0
            for s in self.submissions.approved_by_student(student_id)
        )

    def _decorate(self, submission: Submission) -> dict:
        """Attach the cause name and student id the tables display."""
        cause = self.causes.get_by_id(submission.cause_id)
        student = self.students.get_by_id(submission.student_id)
        return {
            "submission": submission,
            "cause_name": cause.cause_name if cause else "—",
            "cause": cause,
            "student": student,
        }
