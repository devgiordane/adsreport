from __future__ import annotations

from adsreport.constants import SettingKey
from adsreport.services.settings_service import SettingsService


def test_load_config_marks_facebook_credentials_locked_without_password(session):
    with SettingsService() as svc:
        svc.set(SettingKey.FB_APP_ID, "app-id", password="admin-password")
        svc.set(SettingKey.FB_APP_SECRET, "app-secret", password="admin-password")
        svc.set(SettingKey.FB_ACCESS_TOKEN, "token", password="admin-password")

        config = svc.load_config()

    assert config.facebook.credentials_locked is True
    assert config.facebook.app_id == ""
    assert not config.is_facebook_configured()


def test_load_config_decrypts_facebook_credentials_with_password(session):
    with SettingsService() as svc:
        svc.set(SettingKey.FB_APP_ID, "app-id", password="admin-password")
        svc.set(SettingKey.FB_APP_SECRET, "app-secret", password="admin-password")
        svc.set(SettingKey.FB_ACCESS_TOKEN, "token", password="admin-password")

        config = svc.load_config(password="admin-password")

    assert config.facebook.credentials_locked is False
    assert config.facebook.app_id == "app-id"
    assert config.facebook.app_secret == "app-secret"
    assert config.facebook.access_token == "token"
    assert config.is_facebook_configured()
