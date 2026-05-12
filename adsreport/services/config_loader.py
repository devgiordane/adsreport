"""Central config reload — reads DB settings into the global AppConfig object."""

from __future__ import annotations

from adsreport.config import AppConfig, set_config
from adsreport.services.settings_service import SettingsService


def reload_config(password: str | None = None) -> AppConfig:
    """Re-read app_settings from DB and update the global AppConfig."""
    with SettingsService() as svc:
        config = svc.load_config(password=password)
    set_config(config)
    return config
