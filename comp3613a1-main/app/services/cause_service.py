from app.models.submission import VolunteerCause
from app.repositories.submission import VolunteerCauseRepository


class CauseService:
    """The causes list, plus the admin's top-ups.

    Approvals spend a cause's hours (see ReviewService.decide); this service
    owns giving them back.
    """

    def __init__(self, causes: VolunteerCauseRepository):
        self.causes = causes

    def list_causes(self, search: str = "") -> list[VolunteerCause]:
        return self.causes.list_all(search)

    def add_hours(self, *, cause_id: int, hours: float) -> VolunteerCause:
        """Give a cause more hours to offer students."""
        if hours <= 0:
            raise ValueError("Hours to add must be more than zero.")

        cause = self.causes.get_by_id(cause_id)
        if cause is None:
            raise ValueError("That cause no longer exists.")

        return self.causes.adjust_hours(cause_id, hours)
