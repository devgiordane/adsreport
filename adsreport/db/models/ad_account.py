from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adsreport.db.base import Base, TimestampMixin, _new_uuid


class AdAccount(Base, TimestampMixin):
    __tablename__ = "ad_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    fb_account_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="ad_account", lazy="dynamic")  # type: ignore[name-defined]  # noqa: F821
    insights: Mapped[list["Insight"]] = relationship(back_populates="ad_account", lazy="dynamic")  # type: ignore[name-defined]  # noqa: F821
