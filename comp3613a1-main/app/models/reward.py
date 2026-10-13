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
    """TODO(student): complete this table from the ERD block in docs/report.md.

    It is the bridge between Student and Reward. The composite primary key is
    scaffolded exactly as the ERD draws it. Add the other three attributes the
    ERD lists for this entity, using the snake_case style Submission uses for
    the ERD's camelCase names (hoursSpent -> hours_spent). Whatever you add
    has to match what the redeem service sets when a student confirms.
    """

    student_id: int = Field(foreign_key="student.id", primary_key=True)
    reward_id: int = Field(foreign_key="reward.id", primary_key=True)
    charity_id: int = Field(foreign_key="charity.id")
    date_redeemed: date = Field(default_factory=date.today)
    hours_spent: float = Field(default=0.0)
