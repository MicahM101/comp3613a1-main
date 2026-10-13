from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class Reward(SQLModel, table=True):
    """Something a student spends verified hours on (Workflow 3)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    reward_name: str
    hour_cost: float
    # Phase 5 model revision: the wireframe's conversion cards show a rate
    # line ("1hr = $1", "1hr = 1 credit") that name + cost alone cannot hold.
    rate_note: Optional[str] = None


class Charity(SQLModel, table=True):
    """A partner charity a donation conversion is made out to."""

    id: Optional[int] = Field(default=None, primary_key=True)
    charity_name: str


class HoursRedemption(SQLModel, table=True):
    """One redemption a student has made (Workflow 3).

    Phase 5 revision (student's call): the ERD drew this as a composite key
    of studentId + rewardId — one redemption per student per reward, which
    would refuse a second donation outright. The student asked for repeat
    redemptions, so the table carries its own ``id`` and the ERD's other
    attributes, in the snake_case style Submission uses
    (hoursSpent -> hours_spent).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    reward_id: int = Field(foreign_key="reward.id")
    charity_id: Optional[int] = Field(default=None, foreign_key="charity.id")
    date_redeemed: date = Field(default_factory=date.today)
    hours_spent: float
