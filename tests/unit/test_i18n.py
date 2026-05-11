from __future__ import annotations

import json
from pathlib import Path

import pytest

from adsreport.i18n import set_locale, t


def test_translate_ptbr():
    set_locale("pt-BR")
    assert t("common.save") == "Salvar"


def test_translate_enus():
    set_locale("en-US")
    assert t("common.save") == "Save"


def test_missing_key_returns_key():
    set_locale("en-US")
    assert t("nonexistent.key.xyz") == "nonexistent.key.xyz"


def test_interpolation():
    set_locale("en-US")
    result = t("onboarding.step3.connection_ok", count=3)
    assert "3" in result


def test_ptbr_interpolation():
    set_locale("pt-BR")
    result = t("onboarding.step3.connection_fail", error="token expired")
    assert "token expired" in result


def test_key_parity():
    locales_dir = Path(__file__).parent.parent.parent / "adsreport" / "i18n" / "locales"
    en = json.loads((locales_dir / "en-US.json").read_text())
    pt = json.loads((locales_dir / "pt-BR.json").read_text())

    missing_in_pt = set(en.keys()) - set(pt.keys())
    missing_in_en = set(pt.keys()) - set(en.keys())

    assert not missing_in_pt, f"Keys missing in pt-BR: {sorted(missing_in_pt)}"
    assert not missing_in_en, f"Keys missing in en-US: {sorted(missing_in_en)}"
