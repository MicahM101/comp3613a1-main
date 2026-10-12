from typing import Optional

from sqlmodel import Session, select

from app.models.student import Student
from app.models.submission import Submission, VolunteerCause


class StudentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_user_id(self, user_id: int) -> Optional[Student]:
        return self.session.exec(select(Student).where(Student.user_id == user_id)).first()

    def create(self, student: Student) -> Student:
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        return student


class VolunteerCauseRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[VolunteerCause]:
        return self.session.exec(select(VolunteerCause).order_by(VolunteerCause.cause_name)).all()

    def get_by_id(self, cause_id: int) -> Optional[VolunteerCause]:
        return self.session.get(VolunteerCause, cause_id)


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
        ...

    def all_recent(self) -> list[Submission]:
        """Newest first — the queue Workflow 2 reviews."""
        return self.session.exec(select(Submission).order_by(Submission.id.desc())).all()

    def get_by_id(self, submission_id: int) -> Optional[Submission]:
        return self.session.get(Submission, submission_id)
