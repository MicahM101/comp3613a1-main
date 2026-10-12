from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class VolunteerCause(SQLModel, table=True):
    """A cause a student can serve (and later pick on the submission form)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    cause_name: str
    description: str
    hours_available: Optional[float] = None
    date_available: Optional[date] = None


class Submission(SQLModel, table=True):
    """A student's request for hours to be verified (Workflow 1 → Workflow 2).

    Column names are the snake_case equivalents of the ERD attributes
    (studentId → student_id, startTime → start_time, and so on).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    admin_id: Optional[int] = Field(default=None, foreign_key="admin.id")
    cause_id: int = Field(foreign_key="volunteercause.id", index=True)
    hours_completed: float
    date_completed: date
    start_time: Optional[str] = None
    document_path: Optional[str] = None
    state: str = Field(default="pending")  # pending, approved, rejected

