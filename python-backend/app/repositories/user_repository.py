from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_account(self, user_account: str) -> User | None:
        stmt = select(User).where(User.user_account == user_account, User.is_delete == 0)
        return self.db.execute(stmt).scalar_one_or_none()

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
