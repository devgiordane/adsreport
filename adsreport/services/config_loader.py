"""Load runtime configuration from persistent settings."""

from __future__ import annotations

from adsreport.config import AppConfig, set_config
from adsreport.services.settings_service import SettingsService


def reload_config(password: str | None = None) -> AppConfig:
    """Re-read settings from DB and publish the process-global app config."""
    with SettingsService() as service:
        config = service.load_config(password=password)
    set_config(config)
    return config
