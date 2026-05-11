"""i18n public API: t(), set_locale(), current_locale()."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_LOCALES_DIR = Path(__file__).parent / "locales"
_translations: dict[str, dict[str, str]] = {}
_current_locale: str = "pt-BR"


def _load(locale: str) -> dict[str, str]:
    if locale not in _translations:
        path = _LOCALES_DIR / f"{locale}.json"
        if not path.exists():
            return {}
        _translations[locale] = json.loads(path.read_text(encoding="utf-8"))
    return _translations[locale]


def set_locale(locale: str) -> None:
    global _current_locale
    _current_locale = locale
    _load(locale)


def current_locale() -> str:
    return _current_locale


def t(key: str, **kwargs: Any) -> str:
    catalog = _load(_current_locale)
    text = catalog.get(key)
    if text is None:
        fallback = _load("en-US")
        text = fallback.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
