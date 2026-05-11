from __future__ import annotations

from sqlalchemy import select

from adsreport.db.models.user import User
from adsreport.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model_class = User

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.session.scalar(stmt)

    def get_admin(self) -> User | None:
        stmt = select(User).where(User.is_active == True).limit(1)  # noqa: E712
        return self.session.scalar(stmt)

    def exists(self) -> bool:
        stmt = select(User.id).limit(1)
        return self.session.scalar(stmt) is not None
