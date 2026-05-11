from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adsreport.db.base import Base, _new_uuid


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ad_account_id: Mapped[str] = mapped_column(ForeignKey("ad_accounts.id"), nullable=False, index=True)

    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spend_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reach: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    frequency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ctr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cpc_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cpm_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    purchase_value_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    roas: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw_actions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    ad_account: Mapped["AdAccount"] = relationship(back_populates="insights")  # type: ignore[name-defined]  # noqa: F821

    __table_args__ = (
        Index("ix_insights_level_entity_date", "level", "entity_id", "date", unique=True),
        Index("ix_insights_account_date", "ad_account_id", "date"),
    )
