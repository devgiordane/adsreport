from __future__ import annotations

from sqlalchemy import select

from adsreport.db.models.ad_account import AdAccount
from adsreport.repositories.base import BaseRepository


class AdAccountRepository(BaseRepository[AdAccount]):
    model_class = AdAccount

    def get_all(self) -> list[AdAccount]:
        stmt = select(AdAccount).order_by(AdAccount.is_default.desc(), AdAccount.name.asc())
        return list(self.session.scalars(stmt).all())

    def upsert_from_fb(
        self,
        fb_data: dict[str, object],
        fallback_timezone: str = "America/Sao_Paulo",
    ) -> AdAccount:
        fb_account_id = _fb_account_id(fb_data)
        account = self.get_by_fb_id(fb_account_id)
        if account is None:
            account = AdAccount(fb_account_id=fb_account_id, name=fb_account_id)

        account.name = _string_value(fb_data.get("name"), fb_account_id)
        account.currency = _string_value(fb_data.get("currency"), "BRL").upper()[:3]
        account.timezone = _string_value(
            fb_data.get("timezone_name") or fb_data.get("timezone"),
            fallback_timezone,
        )
        account.status = _account_status(fb_data.get("account_status"))
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def get_by_fb_id(self, fb_account_id: str) -> AdAccount | None:
        stmt = select(AdAccount).where(AdAccount.fb_account_id == fb_account_id)
        return self.session.scalar(stmt)

    def get_all_active(self) -> list[AdAccount]:
        stmt = (
            select(AdAccount)
            .where(AdAccount.status == "active")
            .order_by(AdAccount.is_default.desc(), AdAccount.name.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_sync_enabled(self) -> list[AdAccount]:
        stmt = (
            select(AdAccount)
            .where(AdAccount.sync_enabled == True)  # noqa: E712
            .order_by(AdAccount.is_default.desc(), AdAccount.name.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_default(self) -> AdAccount | None:
        stmt = select(AdAccount).where(AdAccount.is_default == True)  # noqa: E712
        return self.session.scalar(stmt)

    def set_default(self, account_id: str) -> None:
        for acct in self.get_all():
            acct.is_default = acct.id == account_id
            if acct.is_default:
                acct.sync_enabled = True
        self.session.commit()

    def set_sync_enabled(self, account_ids: list[str]) -> None:
        selected = set(account_ids)
        for account in self.get_all():
            account.sync_enabled = account.id in selected
        self.session.commit()


def _fb_account_id(fb_data: dict[str, object]) -> str:
    raw = fb_data.get("id") or fb_data.get("account_id")
    fb_account_id = str(raw or "").strip()
    if not fb_account_id:
        raise ValueError("Facebook ad account payload is missing an id.")
    return fb_account_id


def _string_value(value: object, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _account_status(value: object) -> str:
    if value is None:
        return "active"
    normalized = str(value).strip().lower()
    return "active" if normalized in {"1", "active"} else "disabled"
