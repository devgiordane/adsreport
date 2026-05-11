"""Settings service: read/write app_settings table, populate AppConfig."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from adsreport.config import AppConfig, DashboardConfig, FacebookConfig, SyncConfig
from adsreport.constants import SETTING_DEFAULTS, SettingKey
from adsreport.core.crypto import decrypt, encrypt
from adsreport.repositories.settings_repo import SettingsRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


_SECRET_KEYS = {
    SettingKey.FB_ACCESS_TOKEN,
    SettingKey.FB_APP_ID,
    SettingKey.FB_APP_SECRET,
}


class SettingsService:
    def __init__(self, session: Session | None = None) -> None:
        self._repo = SettingsRepository(session)

    def close(self) -> None:
        self._repo.close()

    def __enter__(self) -> SettingsService:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def get(self, key: str, password: str | None = None) -> Any:
        setting = self._repo.get_by_key(key)
        if setting is None:
            return SETTING_DEFAULTS.get(key)
        if setting.is_secret:
            if password is None:
                raise ValueError(f"Password required to read secret: {key}")
            raw = setting.value_encrypted or ""
            return decrypt(raw, password) if raw else ""
        return self._coerce(setting.value_plain, setting.value_type)

    def set(self, key: str, value: Any, password: str | None = None) -> None:
        is_secret = key in _SECRET_KEYS
        if is_secret:
            if password is None:
                raise ValueError(f"Password required to write secret: {key}")
            self._repo.upsert(
                key,
                value_encrypted=encrypt(str(value), password),
                value_plain=None,
                is_secret=True,
                value_type="string",
            )
        else:
            value_type, serialized = self._serialize(value)
            self._repo.upsert(
                key,
                value_plain=serialized,
                value_encrypted=None,
                is_secret=False,
                value_type=value_type,
            )

    def load_config(self, password: str | None = None) -> AppConfig:
        def g(key: str) -> Any:
            return self.get(key, password)

        credentials_locked = password is None and any(
            self._secret_is_set(key) for key in _SECRET_KEYS
        )

        if password is None:
            facebook_access_token = ""
            facebook_app_id = ""
            facebook_app_secret = ""
        else:
            facebook_access_token = g(SettingKey.FB_ACCESS_TOKEN) or ""
            facebook_app_id = g(SettingKey.FB_APP_ID) or ""
            facebook_app_secret = g(SettingKey.FB_APP_SECRET) or ""

        return AppConfig(
            locale=g(SettingKey.LOCALE) or "pt-BR",
            timezone=g(SettingKey.TIMEZONE) or "America/Sao_Paulo",
            onboarding_completed=bool(g(SettingKey.ONBOARDING_COMPLETED)),
            theme=g(SettingKey.THEME) or "dark",
            facebook=FacebookConfig(
                access_token=facebook_access_token,
                app_id=facebook_app_id,
                app_secret=facebook_app_secret,
                api_version=g(SettingKey.FB_API_VERSION) or "v21.0",
                default_account_id=g(SettingKey.FB_DEFAULT_ACCOUNT_ID) or "",
                credentials_locked=credentials_locked,
            ),
            sync=SyncConfig(
                interval_minutes=int(g(SettingKey.SYNC_INTERVAL_MINUTES) or 60),
                lookback_days=int(g(SettingKey.SYNC_LOOKBACK_DAYS) or 30),
                last_run_at=g(SettingKey.SYNC_LAST_RUN_AT),
            ),
            dashboard=DashboardConfig(
                default_range=g(SettingKey.DASHBOARD_DEFAULT_RANGE) or "last_7_days",
                kpis_enabled=g(SettingKey.DASHBOARD_KPIS_ENABLED) or [],
            ),
        )

    def complete_onboarding(self) -> None:
        self.set(SettingKey.ONBOARDING_COMPLETED, True)

    def _secret_is_set(self, key: str) -> bool:
        setting = self._repo.get_by_key(key)
        return bool(setting and setting.is_secret and setting.value_encrypted)

    def _coerce(self, value: str | None, value_type: str) -> Any:
        if value is None:
            return None
        match value_type:
            case "bool":
                return value.lower() in ("true", "1", "yes")
            case "int":
                return int(value)
            case "json":
                return json.loads(value)
            case _:
                return value

    def _serialize(self, value: Any) -> tuple[str, str]:
        if isinstance(value, bool):
            return "bool", str(value).lower()
        if isinstance(value, int):
            return "int", str(value)
        if isinstance(value, (list, dict)):
            return "json", json.dumps(value)
        return "string", str(value)
