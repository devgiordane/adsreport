from __future__ import annotations

from datetime import date

from adsreport.i18n import set_locale
from adsreport.ui.callbacks.filter_callbacks import (
    refresh_account_filter_options,
    refresh_campaign_filter_options,
)
from adsreport.ui.components.filter_bar import filter_bar, period_options
from tests.factories import AdAccountFactory, CampaignFactory, InsightFactory


def test_period_options_are_translated_at_render_time(session):
    set_locale("en-US")
    english_today = period_options()[0]["label"]

    set_locale("pt-BR")
    portuguese_today = period_options()[0]["label"]

    assert english_today != portuguese_today


def test_period_options_include_previous_month(session):
    set_locale("en-US")

    values = [option["value"] for option in period_options()]

    assert "last_month" in values


def test_filter_bar_loads_active_account_options(session):
    active = AdAccountFactory.create(name="Active Client", fb_account_id="act_111")
    disabled = AdAccountFactory.create(name="Disabled Client", fb_account_id="act_222", status="disabled")
    session.add_all([active, disabled])
    session.commit()

    rendered = filter_bar()
    account_dropdown = rendered.children[1]

    assert account_dropdown.options == [
        {"label": "Active Client (act_111)", "value": active.id}
    ]


def test_account_filter_callback_refreshes_options_and_keeps_valid_selection(session):
    active = AdAccountFactory.create(name="Active Client", fb_account_id="act_111")
    other = AdAccountFactory.create(name="Other Client", fb_account_id="act_222")
    disabled = AdAccountFactory.create(name="Disabled Client", fb_account_id="act_333", status="disabled")
    session.add_all([active, other, disabled])
    session.commit()

    options, selected = refresh_account_filter_options(0, 0, [active.id, disabled.id, "missing"])

    assert options == [
        {"label": "Active Client (act_111)", "value": active.id},
        {"label": "Other Client (act_222)", "value": other.id},
    ]
    assert selected == [active.id]


def test_campaign_filter_uses_campaigns_with_delivery_not_only_active(session):
    account = AdAccountFactory.create()
    paused_with_delivery = CampaignFactory.create(
        ad_account_id=account.id,
        fb_campaign_id="camp_paused",
        name="Paused with delivery",
        status="PAUSED",
        effective_status="PAUSED",
    )
    active_without_delivery = CampaignFactory.create(
        ad_account_id=account.id,
        fb_campaign_id="camp_active",
        name="Active without delivery",
        status="ACTIVE",
        effective_status="ACTIVE",
    )
    session.add_all([account, paused_with_delivery, active_without_delivery])
    session.add(
        InsightFactory.create(
            date=date.today(),
            level="campaign",
            ad_account_id=account.id,
            entity_id="camp_paused",
            impressions=10,
        )
    )
    session.add(
        InsightFactory.create(
            date=date.today(),
            level="campaign",
            ad_account_id=account.id,
            entity_id="camp_active",
            impressions=0,
        )
    )
    session.commit()

    options, selected = refresh_campaign_filter_options(
        "last_30_days",
        [account.id],
        0,
        ["camp_paused", "camp_active"],
    )

    assert options == [{"label": "Paused with delivery", "value": "camp_paused"}]
    assert selected == ["camp_paused"]
