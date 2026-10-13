from typing import Optional

from sqlmodel import Session, select

from app.models.admin import Admin


class AdminRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_user_id(self, user_id: int) -> Optional[Admin]:
        return self.session.exec(select(Admin).where(Admin.user_id == user_id)).first()

    def get_by_id(self, admin_id: int) -> Optional[Admin]:
        return self.session.get(Admin, admin_id)

    def create(self, admin: Admin) -> Admin:
        self.session.add(admin)
        self.session.commit()
        self.session.refresh(admin)
        return admin
