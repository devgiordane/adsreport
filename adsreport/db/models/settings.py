from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from adsreport.db.base import Base, _new_uuid


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    value_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_plain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(16), nullable=False, default="string")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
