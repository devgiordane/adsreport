"""Application-wide constants: setting keys, enums, cache names."""

from __future__ import annotations

from enum import Enum


class SupportedLocale(str, Enum):
    PT_BR = "pt-BR"
    EN_US = "en-US"


class Theme(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class SyncStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class InsightLevel(str, Enum):
    ACCOUNT = "account"
    CAMPAIGN = "campaign"
    ADSET = "adset"
    AD = "ad"


class SyncTrigger(str, Enum):
    SCHEDULER = "scheduler"
    MANUAL = "manual"
    ONBOARDING = "onboarding"


class AdAccountStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


# ── Setting keys ─────────────────────────────────────────────────────────────
# Stored in app_settings.key — import these constants instead of bare strings.

class SettingKey:
    # App
    LOCALE = "app.locale"
    TIMEZONE = "app.timezone"
    ONBOARDING_COMPLETED = "app.onboarding_completed"
    THEME = "app.theme"

    # Facebook
    FB_ACCESS_TOKEN = "facebook.access_token"
    FB_APP_ID = "facebook.app_id"
    FB_APP_SECRET = "facebook.app_secret"
    FB_API_VERSION = "facebook.api_version"
    FB_DEFAULT_ACCOUNT_ID = "facebook.default_account_id"

    # Sync
    SYNC_INTERVAL_MINUTES = "sync.interval_minutes"
    SYNC_LOOKBACK_DAYS = "sync.lookback_days"
    SYNC_LAST_RUN_AT = "sync.last_run_at"

    # Dashboard
    DASHBOARD_DEFAULT_RANGE = "dashboard.default_range"
    DASHBOARD_KPIS_ENABLED = "dashboard.kpis_enabled"


# ── Setting defaults ──────────────────────────────────────────────────────────

SETTING_DEFAULTS: dict[str, object] = {
    SettingKey.LOCALE: SupportedLocale.PT_BR,
    SettingKey.TIMEZONE: "America/Sao_Paulo",
    SettingKey.ONBOARDING_COMPLETED: False,
    SettingKey.THEME: Theme.DARK,
    SettingKey.FB_API_VERSION: "v21.0",
    SettingKey.SYNC_INTERVAL_MINUTES: 60,
    SettingKey.SYNC_LOOKBACK_DAYS: 30,
    SettingKey.DASHBOARD_DEFAULT_RANGE: "last_7_days",
    SettingKey.DASHBOARD_KPIS_ENABLED: [
        "impressions", "clicks", "ctr", "cpc", "cpm",
        "spend", "leads", "conversions", "roas",
    ],
}

# ── Cache keys ────────────────────────────────────────────────────────────────

class CacheKey:
    AD_ACCOUNTS = "fb:ad_accounts"
    CAMPAIGN_LIST = "fb:campaigns:{account_id}"
    INSIGHT_SUMMARY = "report:summary:{account_id}:{date_from}:{date_to}"


# ── Job IDs ───────────────────────────────────────────────────────────────────

JOB_SYNC_ID = "ads_sync"
JOB_CLEANUP_ID = "cleanup"

# ── Misc ──────────────────────────────────────────────────────────────────────

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15
PBKDF2_ITERATIONS = 300_000
SALT_FILENAME = ".salt"
FLASK_SECRET_FILENAME = ".flask-secret"
DB_FILENAME = "data.db"
DEFAULT_ADMIN_USERNAME = "admin"
FACEBOOK_API_DEFAULT_VERSION = "v21.0"
