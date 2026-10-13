from typing import Optional

from sqlmodel import Session, select

from app.models.reward import Charity, HoursRedemption, Reward


class RewardRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Reward]:
        """Cheapest first, so the grid reads in a sensible order."""
        return self.session.exec(select(Reward).order_by(Reward.hour_cost)).all()

    def get_by_id(self, reward_id: int) -> Optional[Reward]:
        return self.session.get(Reward, reward_id)


class CharityRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Charity]:
        return self.session.exec(select(Charity).order_by(Charity.charity_name)).all()

    def get_by_id(self, charity_id: int) -> Optional[Charity]:
        return self.session.get(Charity, charity_id)


class HoursRedemptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, redemption: HoursRedemption) -> HoursRedemption:
        self.session.add(redemption)
        self.session.commit()
        self.session.refresh(redemption)
        return redemption

    def by_student(self, student_id: int) -> list[HoursRedemption]:
        return self.session.exec(
            select(HoursRedemption).where(HoursRedemption.student_id == student_id)
        ).all()

    def total_spent(self, student_id: int) -> float:
        """Hours already converted into rewards or donations."""
        return sum(redemption.hours_spent or 0.0 for redemption in self.by_student(student_id))

    def get(self, student_id: int, reward_id: int) -> Optional[HoursRedemption]:
        """Composite key: (student, reward) is one row in the ERD."""
        return self.session.get(HoursRedemption, (student_id, reward_id))
