from __future__ import annotations

from sqlalchemy import select

from adsreport.db.models.ad_account import AdAccount
from adsreport.repositories.base import BaseRepository


class AdAccountRepository(BaseRepository[AdAccount]):
    model_class = AdAccount

    def get_by_fb_id(self, fb_account_id: str) -> AdAccount | None:
        stmt = select(AdAccount).where(AdAccount.fb_account_id == fb_account_id)
        return self.session.scalar(stmt)

    def get_all_active(self) -> list[AdAccount]:
        stmt = select(AdAccount).where(AdAccount.status == "active")
        return list(self.session.scalars(stmt).all())

    def get_default(self) -> AdAccount | None:
        stmt = select(AdAccount).where(AdAccount.is_default == True)  # noqa: E712
        return self.session.scalar(stmt)

    def set_default(self, account_id: str) -> None:
        for acct in self.get_all_active():
            acct.is_default = acct.id == account_id
        self.session.commit()
