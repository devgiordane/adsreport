"""i18n service — thin wrapper kept for service-layer completeness.

Most code should use adsreport.i18n.t() directly.
"""

from __future__ import annotations

from adsreport.i18n import set_locale, t


class I18nService:
    def set_locale(self, locale: str) -> None:
        set_locale(locale)
        from adsreport.constants import SettingKey
        from adsreport.services.settings_service import SettingsService

        SettingsService().set(SettingKey.LOCALE, locale)

    def translate(self, key: str, **kwargs: object) -> str:
        return t(key, **kwargs)
