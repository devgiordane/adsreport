"""Settings service: read/write app_settings table, populate AppConfig."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from adsreport.config import AppConfig, DashboardConfig, FacebookConfig, SyncConfig
from adsreport.constants import SETTING_DEFAULTS, SettingKey
from adsreport.core.crypto import decrypt, decrypt_secret, encrypt, encrypt_secret
from adsreport.core.errors import CryptoError
from adsreport.repositories.settings_repo import SettingsRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from adsreport.db.models.settings import AppSetting


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
            value, _locked = self._decrypt_setting(setting, password)
            return value
        return self._coerce(setting.value_plain, setting.value_type)

    def set(self, key: str, value: Any, password: str | None = None) -> None:
        if key in _SECRET_KEYS:
            if password:
                encrypted = encrypt(str(value), password)
                value_type = "password"
            else:
                encrypted = encrypt_secret(str(value))
                value_type = "string"
            self._repo.upsert(
                key,
                value_encrypted=encrypted,
                value_plain=None,
                is_secret=True,
                value_type=value_type,
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
            return self.get(key)

        app_id, app_id_locked = self._get_secret(SettingKey.FB_APP_ID, password)
        app_secret, app_secret_locked = self._get_secret(SettingKey.FB_APP_SECRET, password)
        access_token, token_locked = self._get_secret(SettingKey.FB_ACCESS_TOKEN, password)
        credentials_locked = app_id_locked or app_secret_locked or token_locked

        return AppConfig(
            locale=g(SettingKey.LOCALE) or "pt-BR",
            timezone=g(SettingKey.TIMEZONE) or "America/Sao_Paulo",
            onboarding_completed=bool(g(SettingKey.ONBOARDING_COMPLETED)),
            theme="light",
            facebook=FacebookConfig(
                access_token=access_token if not credentials_locked else "",
                app_id=app_id if not credentials_locked else "",
                app_secret=app_secret if not credentials_locked else "",
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

    def _get_secret(self, key: str, password: str | None) -> tuple[str, bool]:
        setting = self._repo.get_by_key(key)
        if setting is None:
            return "", False
        return self._decrypt_setting(setting, password)

    def _decrypt_setting(self, setting: AppSetting, password: str | None) -> tuple[str, bool]:
        raw = setting.value_encrypted or ""
        if not raw:
            return "", False

        if setting.value_type == "password":
            if not password:
                return "", True
            try:
                return decrypt(raw, password), False
            except CryptoError:
                return "", True

        try:
            return decrypt_secret(raw), False
        except CryptoError:
            return "", True

    def complete_onboarding(self) -> None:
        self.set(SettingKey.ONBOARDING_COMPLETED, True)

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
