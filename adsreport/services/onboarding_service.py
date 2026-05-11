"""Onboarding wizard orchestration."""

from __future__ import annotations

from adsreport.constants import SettingKey
from adsreport.core.errors import OnboardingError, ValidationError
from adsreport.core.result import Err, Ok, Result
from adsreport.services.auth_service import AuthService
from adsreport.services.facebook_client import FacebookClient
from adsreport.services.settings_service import SettingsService


class OnboardingService:
    def __init__(self) -> None:
        self._settings = SettingsService()
        self._auth = AuthService()

    def is_completed(self) -> bool:
        return bool(self._settings.get(SettingKey.ONBOARDING_COMPLETED))

    def save_locale(self, locale: str) -> None:
        self._settings.set(SettingKey.LOCALE, locale)

    def create_admin(self, username: str, password: str, confirm: str) -> Result[None, ValidationError]:
        if password != confirm:
            return Err(ValidationError("confirm_password", "Passwords do not match."))
        result = self._auth.create_admin(username, password)
        if result.is_err():
            return result  # type: ignore[return-value]
        return Ok(None)

    def test_facebook_connection(
        self, app_id: str, app_secret: str, access_token: str
    ) -> Result[list[dict[str, object]], str]:
        try:
            client = FacebookClient(app_id, app_secret, access_token)
            accounts = client.get_ad_accounts()
            return Ok(accounts)
        except Exception as exc:
            return Err(str(exc))

    def save_facebook_credentials(
        self, app_id: str, app_secret: str, access_token: str, password: str
    ) -> None:
        self._settings.set(SettingKey.FB_APP_ID, app_id, password)
        self._settings.set(SettingKey.FB_APP_SECRET, app_secret, password)
        self._settings.set(SettingKey.FB_ACCESS_TOKEN, access_token, password)

    def save_default_account(self, fb_account_id: str, timezone: str) -> None:
        self._settings.set(SettingKey.FB_DEFAULT_ACCOUNT_ID, fb_account_id)
        self._settings.set(SettingKey.TIMEZONE, timezone)

        from adsreport.db.models.ad_account import AdAccount
        from adsreport.repositories.ad_account_repo import AdAccountRepository

        repo = AdAccountRepository()
        existing = repo.get_by_fb_id(fb_account_id)
        if existing is None:
            account = AdAccount(fb_account_id=fb_account_id, name=fb_account_id, timezone=timezone)
            repo.save(account)
        repo.set_default(existing.id if existing else repo.get_by_fb_id(fb_account_id).id)  # type: ignore[union-attr]

    def save_preferences(
        self,
        kpis: list[str],
        default_range: str,
        theme: str,
        sync_interval: int,
    ) -> None:
        self._settings.set(SettingKey.DASHBOARD_KPIS_ENABLED, kpis)
        self._settings.set(SettingKey.DASHBOARD_DEFAULT_RANGE, default_range)
        self._settings.set(SettingKey.THEME, theme)
        self._settings.set(SettingKey.SYNC_INTERVAL_MINUTES, sync_interval)

    def complete(self) -> None:
        self._settings.complete_onboarding()

        from adsreport.config import reload_config

        reload_config()
        self._trigger_initial_sync()

    def _trigger_initial_sync(self) -> None:
        from adsreport.constants import SyncTrigger
        from adsreport.core.time import date_range
        from adsreport.services.scheduler_service import SchedulerService

        scheduler = SchedulerService()
        scheduler.trigger_sync_now(triggered_by=SyncTrigger.ONBOARDING)
