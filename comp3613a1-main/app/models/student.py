from typing import Optional

from sqlmodel import Field, SQLModel


class Student(SQLModel, table=True):
    """A student profile, linked to the login account in ``user``."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    name: str
    email: str
