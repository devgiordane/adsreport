from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from adsreport.db.models.campaign import Campaign
from adsreport.db.models.insight import Insight
from adsreport.repositories.base import BaseRepository

if TYPE_CHECKING:
    from datetime import date


class InsightRepository(BaseRepository[Insight]):
    model_class = Insight

    def get_by_entity_date(
        self,
        level: str,
        entity_id: str,
        dt: date,
        ad_account_id: str | None = None,
    ) -> Insight | None:
        filters = [
            Insight.level == level,
            Insight.entity_id == entity_id,
            Insight.date == dt,
        ]
        if ad_account_id is not None:
            filters.append(Insight.ad_account_id == ad_account_id)
        stmt = select(Insight).where(and_(*filters))
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

    def get_by_accounts_range(
        self,
        ad_account_ids: list[str],
        date_from: date,
        date_to: date,
        level: str = "campaign",
        entity_ids: list[str] | None = None,
    ) -> list[Insight]:
        if not ad_account_ids:
            return []
        filters = [
            Insight.ad_account_id.in_(ad_account_ids),
            Insight.level == level,
            Insight.date >= date_from,
            Insight.date <= date_to,
        ]
        if entity_ids:
            filters.append(Insight.entity_id.in_(entity_ids))
        stmt = (
            select(Insight)
            .where(and_(*filters))
            .order_by(Insight.date)
        )
        return list(self.session.scalars(stmt).all())

    def get_delivered_campaign_options(
        self,
        ad_account_ids: list[str],
        date_from: date,
        date_to: date,
    ) -> list[dict[str, str]]:
        if not ad_account_ids:
            return []

        stmt = (
            select(Insight.entity_id, Campaign.name)
            .outerjoin(
                Campaign,
                and_(
                    Campaign.fb_campaign_id == Insight.entity_id,
                    Campaign.ad_account_id == Insight.ad_account_id,
                ),
            )
            .where(
                and_(
                    Insight.ad_account_id.in_(ad_account_ids),
                    Insight.level == "campaign",
                    Insight.date >= date_from,
                    Insight.date <= date_to,
                    Insight.impressions > 0,
                )
            )
            .distinct()
            .order_by(Campaign.name.asc(), Insight.entity_id.asc())
        )
        return [
            {
                "label": name or entity_id,
                "value": entity_id,
            }
            for entity_id, name in self.session.execute(stmt)
        ]

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
            index_elements=["ad_account_id", "level", "entity_id", "date"],
            set_=update_values,
        )
        self.session.execute(stmt)
        self.session.commit()
        self.session.expire_all()
        saved = self.get_by_entity_date(
            insight.level,
            insight.entity_id,
            insight.date,
            insight.ad_account_id,
        )
        if saved is None:
            raise RuntimeError("Insight upsert succeeded but row could not be loaded.")
        return saved

    def _select_then_upsert(self, insight: Insight) -> Insight:
        existing = self.get_by_entity_date(
            insight.level,
            insight.entity_id,
            insight.date,
            insight.ad_account_id,
        )
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
