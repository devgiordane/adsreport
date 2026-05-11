from __future__ import annotations

from datetime import datetime

import flask_login
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from adsreport.db.base import Base, TimestampMixin, _new_uuid


class User(Base, TimestampMixin, flask_login.UserMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferred_locale: Mapped[str] = mapped_column(String(8), default="pt-BR", nullable=False)

    def get_id(self) -> str:
        return self.id
