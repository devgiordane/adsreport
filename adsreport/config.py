"""Runtime configuration loaded from app_settings table.

AppConfig is a plain dataclass populated at startup by ConfigService.
UI and services read from this object — never from env vars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adsreport.constants import (
    FACEBOOK_API_DEFAULT_VERSION,
    SettingKey,
    SupportedLocale,
    Theme,
)


@dataclass
class FacebookConfig:
    access_token: str = ""
    app_id: str = ""
    app_secret: str = ""
    api_version: str = FACEBOOK_API_DEFAULT_VERSION
    default_account_id: str = ""
    credentials_locked: bool = False


@dataclass
class SyncConfig:
    interval_minutes: int = 60
    lookback_days: int = 30
    last_run_at: str | None = None


@dataclass
class DashboardConfig:
    default_range: str = "last_7_days"
    kpis_enabled: list[str] = field(default_factory=lambda: [
        "impressions", "clicks", "ctr", "cpc", "cpm",
        "spend", "leads", "conversions", "roas",
    ])


@dataclass
class AppConfig:
    locale: str = SupportedLocale.PT_BR
    timezone: str = "America/Sao_Paulo"
    onboarding_completed: bool = False
    theme: str = Theme.DARK
    facebook: FacebookConfig = field(default_factory=FacebookConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)

    def is_facebook_configured(self) -> bool:
        return bool(
            not self.facebook.credentials_locked
            and self.facebook.access_token
            and self.facebook.app_id
            and self.facebook.app_secret
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            SettingKey.LOCALE: self.locale,
            SettingKey.TIMEZONE: self.timezone,
            SettingKey.ONBOARDING_COMPLETED: self.onboarding_completed,
            SettingKey.THEME: self.theme,
            SettingKey.FB_ACCESS_TOKEN: self.facebook.access_token,
            SettingKey.FB_APP_ID: self.facebook.app_id,
            SettingKey.FB_APP_SECRET: self.facebook.app_secret,
            SettingKey.FB_API_VERSION: self.facebook.api_version,
            SettingKey.FB_DEFAULT_ACCOUNT_ID: self.facebook.default_account_id,
            SettingKey.SYNC_INTERVAL_MINUTES: self.sync.interval_minutes,
            SettingKey.SYNC_LOOKBACK_DAYS: self.sync.lookback_days,
            SettingKey.DASHBOARD_DEFAULT_RANGE: self.dashboard.default_range,
            SettingKey.DASHBOARD_KPIS_ENABLED: self.dashboard.kpis_enabled,
        }


_config: AppConfig | None = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def set_config(config: AppConfig) -> None:
    global _config
    _config = config
