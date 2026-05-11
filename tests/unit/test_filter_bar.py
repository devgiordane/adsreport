from __future__ import annotations

from adsreport.i18n import set_locale
from adsreport.ui.components.filter_bar import period_options


def test_period_options_are_translated_at_render_time(session):
    set_locale("en-US")
    english_today = period_options()[0]["label"]

    set_locale("pt-BR")
    portuguese_today = period_options()[0]["label"]

    assert english_today != portuguese_today
