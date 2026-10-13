from datetime import date

from app.models.reward import HoursRedemption
from app.models.user import User
from app.repositories.reward import (
    CharityRepository,
    HoursRedemptionRepository,
    RewardRepository,
)
from app.repositories.submission import StudentRepository, SubmissionRepository


class RedeemService:
    """Workflow 3 — RedeemProgress: what a student can afford, and spending it."""

    # Phase 4: only Charity Conversion asks for extra input before confirming;
    # every other reward's Select goes straight to the confirmation dialog.
    CHARITY_REWARD_NAME = "Charity Conversion"

    def __init__(
        self,
        rewards: RewardRepository,
        charities: CharityRepository,
        redemptions: HoursRedemptionRepository,
        submissions: SubmissionRepository,
        students: StudentRepository,
    ):
        self.rewards = rewards
        self.charities = charities
        self.redemptions = redemptions
        self.submissions = submissions
        self.students = students

    # --- what the student has -----------------------------------------------

    def available_hours(self, user: User) -> float:
        """Approved hours minus what has already been spent — never stored."""
        student = self.students.get_by_user_id(user.id)
        if student is None:
            return 0.0
        earned = sum(
            submission.hours_completed or 0.0
            for submission in self.submissions.approved_by_student(student.id)
        )
        return earned - self.redemptions.total_spent(student.id)

    # --- the grid ------------------------------------------------------------

    def grid(self, user: User) -> dict:
        """Reward cards plus the affordability flag the wireframe's Select needs."""
        total = self.available_hours(user)
        rows = [
            {
                "reward": reward,
                "affordable": reward.hour_cost <= total,
                "needs": max(reward.hour_cost - total, 0.0),
            }
            for reward in self.rewards.list_all()
        ]
        return {"rewards": rows, "total": total}

    # --- picking one ----------------------------------------------------------

    def start(self, reward_id: int, user: User) -> dict | None:
        """Open a reward — or refuse it (student's choice A: can't start short)."""
        reward = self.rewards.get_by_id(reward_id)
        if reward is None:
            return None

        total = self.available_hours(user)
        if reward.hour_cost > total:
            raise ValueError(
                f"You need {reward.hour_cost - total:g} more hours for {reward.reward_name}."
            )

        return {
            "reward": reward,
            "total": total,
            "is_charity": reward.reward_name == self.CHARITY_REWARD_NAME,
            "charities": self.charities.list_all(),
        }

    def confirm(
        self,
        *,
        reward_id: int,
        user: User,
        hours: float | None = None,
        charity_id: int | None = None,
    ) -> dict:
        """Validate the pick and build what the confirmation screen shows."""
        reward = self.rewards.get_by_id(reward_id)
        if reward is None:
            raise ValueError("That reward no longer exists.")

        total = self.available_hours(user)
        charity = None

        if reward.reward_name == self.CHARITY_REWARD_NAME:
            if hours is None:
                raise ValueError("Choose how many hours to convert.")
            charity = self.charities.get_by_id(charity_id) if charity_id else None
            if charity is None:
                raise ValueError("Choose a partner charity.")
        else:
            hours = reward.hour_cost

        if hours <= 0:
            raise ValueError("Choose more than zero hours.")
        if hours > total:
            raise ValueError(f"You only have {total:g} hours available.")

        return {"reward": reward, "hours": hours, "charity": charity, "total": total}

    # --- spending it ----------------------------------------------------------

    def redeem(
        self,
        *,
        user: User,
        reward_id: int,
        hours: float | None = None,
        charity_id: int | None = None,
    ) -> HoursRedemption:
        """Record the redemption once the student has confirmed it."""
        student = self.students.get_by_user_id(user.id)
        if student is None:
            raise ValueError("This account has no student profile.")

        quote = self.confirm(
            reward_id=reward_id, user=user, hours=hours, charity_id=charity_id
        )

        # The ERD's composite key allows one redemption per student per reward.
        if self.redemptions.get(student.id, reward_id) is not None:
            raise ValueError("You have already redeemed this reward.")

        charity = quote["charity"]
        return self.redemptions.add(
            HoursRedemption(
                student_id=student.id,
                reward_id=reward_id,
                charity_id=charity.id if charity else None,
                date_redeemed=date.today(),
                hours_spent=quote["hours"],
            )
        )
