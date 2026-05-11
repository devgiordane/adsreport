from __future__ import annotations

from sqlalchemy import select

from adsreport.db.models.settings import AppSetting
from adsreport.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[AppSetting]):
    model_class = AppSetting

    def get_by_key(self, key: str) -> AppSetting | None:
        stmt = select(AppSetting).where(AppSetting.key == key)
        return self.session.scalar(stmt)

    def get_all(self) -> list[AppSetting]:
        stmt = select(AppSetting)
        return list(self.session.scalars(stmt).all())

    def get_all_secrets(self) -> list[AppSetting]:
        stmt = select(AppSetting).where(AppSetting.is_secret == True)  # noqa: E712
        return list(self.session.scalars(stmt).all())

    def upsert(self, key: str, **kwargs: object) -> AppSetting:
        setting = self.get_by_key(key)
        if setting is None:
            setting = AppSetting(key=key)
        for k, v in kwargs.items():
            setattr(setting, k, v)
        return self.save(setting)
