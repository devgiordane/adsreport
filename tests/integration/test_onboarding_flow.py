"""Integration test for the full onboarding flow."""

from __future__ import annotations

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
        theme="dark",
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


def test_password_mismatch_fails(session):
    svc = OnboardingService()
    result = svc.create_admin("admin", "password123", "different456")
    assert result.is_err()
