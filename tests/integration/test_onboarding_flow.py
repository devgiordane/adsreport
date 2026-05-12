"""Integration test for the full onboarding flow."""

from __future__ import annotations

from adsreport.config import AppConfig, FacebookConfig, set_config
from adsreport.services.onboarding_service import OnboardingService


def test_onboarding_not_completed_by_default(session):
    svc = OnboardingService()
    assert not svc.is_completed()


def test_complete_onboarding_sets_flag(session):
    svc = OnboardingService()
    # Step 1: locale
    svc.save_locale("pt-BR")
    # Step 2: admin account
    result = svc.create_admin("admin", "securepassword1", "securepassword1")
    assert result.is_ok()
    # Step 5: preferences (skipping FB steps which require live API)
    svc.save_preferences(
        kpis=["impressions", "clicks", "spend"],
        default_range="last_7_days",
        sync_interval=60,
    )
    # Complete (without triggering actual sync)
    from adsreport.constants import SettingKey
    from adsreport.services.settings_service import SettingsService

    with SettingsService() as settings:
        settings.set(SettingKey.ONBOARDING_COMPLETED, True)

    from adsreport.services.config_loader import reload_config

    config = reload_config()
    assert config.onboarding_completed is True


def test_onboarding_saves_all_ad_accounts_and_marks_default(session):
    svc = OnboardingService()

    saved = svc.save_ad_accounts(
        [
            {
                "id": "act_111",
                "name": "Client One",
                "currency": "BRL",
                "timezone_name": "America/Sao_Paulo",
                "account_status": 1,
            },
            {
                "id": "act_222",
                "name": "Client Two",
                "currency": "USD",
                "timezone_name": "America/New_York",
                "account_status": 1,
            },
        ],
        default_fb_account_id="act_222",
    )

    from adsreport.repositories.ad_account_repo import AdAccountRepository

    repo = AdAccountRepository(session)
    accounts = repo.get_all()
    default = repo.get_default()

    assert len(saved) == 2
    assert [account.fb_account_id for account in accounts] == ["act_222", "act_111"]
    assert default is not None
    assert default.fb_account_id == "act_222"
    assert default.name == "Client Two"


def test_refresh_ad_accounts_from_saved_credentials_updates_account_names(session, monkeypatch):
    class FakeFacebookClient:
        def __init__(self, app_id: str, app_secret: str, access_token: str, api_version: str) -> None:
            self.app_id = app_id
            self.app_secret = app_secret
            self.access_token = access_token
            self.api_version = api_version

        def get_ad_accounts(self) -> list[dict[str, object]]:
            return [
                {
                    "id": "act_111",
                    "name": "Real Client Name",
                    "currency": "BRL",
                    "timezone_name": "America/Sao_Paulo",
                    "account_status": 1,
                }
            ]

    monkeypatch.setattr("adsreport.services.onboarding_service.FacebookClient", FakeFacebookClient)
    set_config(
        AppConfig(
            facebook=FacebookConfig(
                app_id="app-id",
                app_secret="secret",
                access_token="token",
                default_account_id="act_111",
            )
        )
    )

    svc = OnboardingService()
    result = svc.refresh_ad_accounts_from_saved_credentials()

    from adsreport.repositories.ad_account_repo import AdAccountRepository

    account = AdAccountRepository(session).get_by_fb_id("act_111")
    assert result.is_ok()
    assert account is not None
    assert account.name == "Real Client Name"
    set_config(AppConfig())


def test_password_mismatch_fails(session):
    svc = OnboardingService()
    result = svc.create_admin("admin", "password123", "different456")
    assert result.is_err()
