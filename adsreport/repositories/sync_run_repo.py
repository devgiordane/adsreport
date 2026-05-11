from __future__ import annotations

from sqlalchemy import desc, select

from adsreport.db.models.sync_run import SyncRun
from adsreport.repositories.base import BaseRepository


class SyncRunRepository(BaseRepository[SyncRun]):
    model_class = SyncRun

    def get_latest(self, ad_account_id: str) -> SyncRun | None:
        stmt = (
            select(SyncRun)
            .where(SyncRun.ad_account_id == ad_account_id)
            .order_by(desc(SyncRun.started_at))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_running(self, ad_account_id: str) -> SyncRun | None:
        stmt = select(SyncRun).where(
            SyncRun.ad_account_id == ad_account_id,
            SyncRun.status == "running",
        )
        return self.session.scalar(stmt)

    def get_recent(self, ad_account_id: str, limit: int = 20) -> list[SyncRun]:
        stmt = (
            select(SyncRun)
            .where(SyncRun.ad_account_id == ad_account_id)
            .order_by(desc(SyncRun.started_at))
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())
