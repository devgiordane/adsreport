from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adsreport.db.base import Base, TimestampMixin, _new_uuid


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    fb_campaign_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    ad_account_id: Mapped[str] = mapped_column(ForeignKey("ad_accounts.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    objective: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    effective_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    daily_budget_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lifetime_budget_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stop_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ad_account: Mapped["AdAccount"] = relationship(back_populates="campaigns")  # type: ignore[name-defined]  # noqa: F821
    adsets: Mapped[list["AdSet"]] = relationship(back_populates="campaign", lazy="dynamic")  # type: ignore[name-defined]  # noqa: F821
