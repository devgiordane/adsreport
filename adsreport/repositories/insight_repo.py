from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from adsreport.db.models.insight import Insight
from adsreport.repositories.base import BaseRepository

if TYPE_CHECKING:
    from datetime import date


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
        bind = self.session.get_bind()
        insert_fn = {
            "sqlite": sqlite_insert,
            "postgresql": postgresql_insert,
        }.get(bind.dialect.name)

        if insert_fn is None:
            return self._select_then_upsert(insight)

        values = {
            column.name: getattr(insight, column.name)
            for column in Insight.__table__.columns
            if column.name != "id" or getattr(insight, column.name, None)
        }
        stmt = cast("Any", insert_fn(Insight).values(**values))
        update_values = {
            column.name: getattr(stmt.excluded, column.name)
            for column in Insight.__table__.columns
            if column.name != "id"
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["level", "entity_id", "date"],
            set_=update_values,
        )
        self.session.execute(stmt)
        self.session.commit()
        self.session.expire_all()
        saved = self.get_by_entity_date(insight.level, insight.entity_id, insight.date)
        if saved is None:
            raise RuntimeError("Insight upsert succeeded but row could not be loaded.")
        return saved

    def _select_then_upsert(self, insight: Insight) -> Insight:
        existing = self.get_by_entity_date(insight.level, insight.entity_id, insight.date)
        if existing is None:
            return self.save(insight)
        for column in Insight.__table__.columns:
            if column.name != "id":
                setattr(existing, column.name, getattr(insight, column.name))
        self.session.commit()
        return existing

    def has_data_for_account(self, ad_account_id: str) -> bool:
        stmt = select(Insight.id).where(Insight.ad_account_id == ad_account_id).limit(1)
        return self.session.scalar(stmt) is not None
