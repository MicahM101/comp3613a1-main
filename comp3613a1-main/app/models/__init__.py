"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.student import Student
from app.models.admin import Admin
from app.models.submission import Submission, VolunteerCause

__all__ = ["User", "Student", "Admin", "Submission", "VolunteerCause"]
