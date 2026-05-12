"""Onboarding wizard orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from adsreport.constants import SettingKey, Theme
from adsreport.core.errors import ValidationError
from adsreport.core.result import Err, Ok, Result
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.services.auth_service import AuthService
from adsreport.services.facebook_client import FacebookClient
from adsreport.services.settings_service import SettingsService

if TYPE_CHECKING:
    from adsreport.db.models.ad_account import AdAccount


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

    def refresh_ad_accounts_from_saved_credentials(self) -> Result[list[AdAccount], str]:
        from adsreport.config import get_config
        from adsreport.services.config_loader import reload_config

        config = get_config()
        if not config.is_facebook_configured() and not config.facebook.credentials_locked:
            config = reload_config()
        if config.facebook.credentials_locked:
            return Err("As credenciais do Facebook estão bloqueadas. Faça login novamente.")
        if not config.is_facebook_configured():
            return Err("Configure App ID, App Secret e Access Token antes de buscar contas.")

        try:
            client = FacebookClient(
                config.facebook.app_id,
                config.facebook.app_secret,
                config.facebook.access_token,
                config.facebook.api_version,
            )
            accounts = client.get_ad_accounts()
            saved_accounts = self.save_ad_accounts(
                accounts,
                default_fb_account_id=config.facebook.default_account_id or None,
                fallback_timezone=config.timezone,
            )
            return Ok(saved_accounts)
        except Exception as exc:
            return Err(str(exc))

    def save_facebook_credentials(
        self, app_id: str, app_secret: str, access_token: str
    ) -> None:
        self._settings.set(SettingKey.FB_APP_ID, app_id)
        self._settings.set(SettingKey.FB_APP_SECRET, app_secret)
        self._settings.set(SettingKey.FB_ACCESS_TOKEN, access_token)

        from adsreport.services.config_loader import reload_config

        reload_config()

    def save_default_account(self, fb_account_id: str, timezone: str) -> None:
        self.save_ad_accounts(
            [{"id": fb_account_id, "name": fb_account_id, "timezone_name": timezone}],
            default_fb_account_id=fb_account_id,
            fallback_timezone=timezone,
        )

    def save_ad_accounts(
        self,
        fb_accounts: list[dict[str, object]],
        default_fb_account_id: str | None = None,
        fallback_timezone: str = "America/Sao_Paulo",
    ) -> list[AdAccount]:
        if not fb_accounts and not default_fb_account_id:
            return []

        saved_accounts: list[AdAccount] = []
        with AdAccountRepository() as repo:
            for raw_account in fb_accounts:
                saved_accounts.append(repo.upsert_from_fb(raw_account, fallback_timezone))

            default_fb_account_id = default_fb_account_id or self._current_or_first_account_id(fb_accounts)
            default_account = repo.get_by_fb_id(default_fb_account_id) if default_fb_account_id else None
            if default_account is not None:
                repo.set_default(default_account.id)
                self._settings.set(SettingKey.FB_DEFAULT_ACCOUNT_ID, default_account.fb_account_id)
                self._settings.set(SettingKey.TIMEZONE, default_account.timezone)

        return saved_accounts

    def _current_or_first_account_id(self, fb_accounts: list[dict[str, object]]) -> str | None:
        existing_default = self._settings.get(SettingKey.FB_DEFAULT_ACCOUNT_ID)
        account_ids = [
            str(account.get("id") or account.get("account_id") or "")
            for account in fb_accounts
        ]
        if existing_default in account_ids:
            return str(existing_default)
        for account_id in account_ids:
            if account_id:
                return account_id
        return None

    def save_preferences(
        self,
        kpis: list[str],
        default_range: str,
        sync_interval: int,
    ) -> None:
        self._settings.set(SettingKey.DASHBOARD_KPIS_ENABLED, kpis)
        self._settings.set(SettingKey.DASHBOARD_DEFAULT_RANGE, default_range)
        self._settings.set(SettingKey.THEME, Theme.LIGHT)
        self._settings.set(SettingKey.SYNC_INTERVAL_MINUTES, sync_interval)

    def complete(self) -> None:
        self._settings.complete_onboarding()

        from adsreport.services.config_loader import reload_config

        reload_config()
        self._trigger_initial_sync()

    def _trigger_initial_sync(self) -> None:
        from adsreport.constants import SyncTrigger
        from adsreport.services.scheduler_service import SchedulerService

        scheduler = SchedulerService()
        scheduler.trigger_sync_now(triggered_by=SyncTrigger.ONBOARDING)
