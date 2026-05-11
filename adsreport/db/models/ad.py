from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adsreport.db.base import Base, TimestampMixin, _new_uuid


class Ad(Base, TimestampMixin):
    __tablename__ = "ads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    fb_ad_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    adset_id: Mapped[str] = mapped_column(ForeignKey("adsets.id"), nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    ad_account_id: Mapped[str] = mapped_column(ForeignKey("ad_accounts.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    effective_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    creative_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    adset: Mapped["AdSet"] = relationship(back_populates="ads")  # type: ignore[name-defined]  # noqa: F821
