from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adsreport.db.base import Base, TimestampMixin, _new_uuid


class AdSet(Base, TimestampMixin):
    __tablename__ = "adsets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    fb_adset_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    ad_account_id: Mapped[str] = mapped_column(ForeignKey("ad_accounts.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    effective_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    daily_budget_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lifetime_budget_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    optimization_goal: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    billing_event: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="adsets")  # type: ignore[name-defined]  # noqa: F821
    ads: Mapped[list["Ad"]] = relationship(back_populates="adset", lazy="dynamic")  # type: ignore[name-defined]  # noqa: F821
