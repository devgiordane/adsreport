from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select

from adsreport.db.models.insight import Insight
from adsreport.repositories.base import BaseRepository


class InsightRepository(BaseRepository[Insight]):
    model_class = Insight

    def get_by_entity_date(self, level: str, entity_id: str, dt: date) -> Insight | None:
        stmt = select(Insight).where(
            and_(
                Insight.level == level,
                Insight.entity_id == entity_id,
                Insight.date == dt,
            )
        )
        return self.session.scalar(stmt)

    def get_by_account_range(
        self,
        ad_account_id: str,
        date_from: date,
        date_to: date,
        level: str = "campaign",
    ) -> list[Insight]:
        stmt = (
            select(Insight)
            .where(
                and_(
                    Insight.ad_account_id == ad_account_id,
                    Insight.level == level,
                    Insight.date >= date_from,
                    Insight.date <= date_to,
                )
            )
            .order_by(Insight.date)
        )
        return list(self.session.scalars(stmt).all())

    def upsert(self, insight: Insight) -> Insight:
        existing = self.get_by_entity_date(insight.level, insight.entity_id, insight.date)
        if existing:
            for col in Insight.__table__.columns:
                if col.name not in ("id",):
                    setattr(existing, col.name, getattr(insight, col.name))
            self.session.commit()
            return existing
        return self.save(insight)

    def has_data_for_account(self, ad_account_id: str) -> bool:
        stmt = select(Insight.id).where(Insight.ad_account_id == ad_account_id).limit(1)
        return self.session.scalar(stmt) is not None
