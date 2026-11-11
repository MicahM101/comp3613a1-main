"""Response shapes for the read-only JSON API (`/api/...`).

Plain SQLModel output schemas — no password or internal columns.
"""

from datetime import date
from typing import Optional

from sqlmodel import SQLModel


class CauseResponse(SQLModel):
    id: int
    cause_name: str
    description: str
    hours_available: Optional[float] = None
    date_available: Optional[date] = None


class RewardResponse(SQLModel):
    id: int
    reward_name: str
    hour_cost: float
    rate_note: Optional[str] = None
    # Affordability for the signed-in student (grid() already computes it).
    affordable: bool = False
    hours_needed: float = 0.0


class SubmissionResponse(SQLModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    cause_id: int
    cause_name: str
    hours_completed: float
    date_completed: date
    start_time: Optional[str] = None
    state: str
    document_path: Optional[str] = None
    original_document_name: Optional[str] = None
