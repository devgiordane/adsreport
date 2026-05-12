from __future__ import annotations

from datetime import date, timedelta

from adsreport.services.report_service import ReportService
from tests.factories import AdAccountFactory, AdSetFactory, CampaignFactory, InsightFactory


def _seed_insights(session, account_id: str, days: int = 7, entity_id: str = "camp_001") -> None:
    today = date.today()
    for i in range(days):
        insight = InsightFactory.create(
            date=today - timedelta(days=i),
            level="campaign",
            ad_account_id=account_id,
            entity_id=entity_id,
            impressions=1000,
            clicks=50,
            spend_cents=5000,
            leads=5,
            conversions=2,
            purchase_value_cents=0,
        )
        session.add(insight)
    session.commit()


def test_get_dashboard_data_no_data(session):
    account = AdAccountFactory.create()
    session.add(account)
    session.commit()

    report = ReportService().get_dashboard_data(account.id, date.today() - timedelta(7), date.today())
    assert not report.has_data


def test_get_dashboard_data_with_data(session):
    account = AdAccountFactory.create()
    campaign = CampaignFactory.create(
        ad_account_id=account.id,
        fb_campaign_id="camp_001",
        name="Leads Maio",
    )
    adset = AdSetFactory.create(
        ad_account_id=account.id,
        campaign_id=campaign.id,
        fb_adset_id="adset_001",
        name="Lookalike 3%",
    )
    session.add(account)
    session.add(campaign)
    session.add(adset)
    session.commit()
    _seed_insights(session, account.id, days=7)
    session.add(
        InsightFactory.create(
            date=date.today(),
            level="adset",
            ad_account_id=account.id,
            entity_id="adset_001",
            impressions=2000,
            clicks=100,
            spend_cents=25000,
            leads=25,
            purchase_value_cents=0,
        )
    )
    session.commit()

    report = ReportService().get_dashboard_data(
        account.id,
        date.today() - timedelta(days=6),
        date.today(),
    )
    assert report.has_data
    assert report.summary.impressions == 7000
    assert report.summary.spend_cents == 35000
    assert report.summary.leads == 35
    assert report.summary.cost_per_lead_cents == 1000
    assert not report.summary.has_roas
    assert len(report.time_series) == 7
    assert len(report.top_campaigns) == 1
    assert report.top_campaigns[0].name == "Leads Maio"
    assert report.top_campaigns[0].cost_per_lead_cents == 1000
    assert report.top_adsets[0].name == "Lookalike 3%"
    assert report.top_adsets[0].leads == 25


def test_get_dashboard_data_for_multiple_accounts(session):
    account_one = AdAccountFactory.create()
    account_two = AdAccountFactory.create()
    session.add_all([account_one, account_two])
    session.commit()
    _seed_insights(session, account_one.id, days=2, entity_id="camp_001")
    _seed_insights(session, account_two.id, days=2, entity_id="camp_002")

    report = ReportService().get_dashboard_data_for_accounts(
        [account_one.id, account_two.id],
        date.today() - timedelta(days=1),
        date.today(),
    )

    assert report.has_data
    assert report.summary.impressions == 4000
    assert report.summary.spend_cents == 20000
    assert len(report.time_series) == 2


def test_get_dashboard_data_uses_explicit_comparison_period(session):
    account = AdAccountFactory.create()
    session.add(account)
    session.add(
        InsightFactory.create(
            date=date(2026, 4, 15),
            level="campaign",
            ad_account_id=account.id,
            entity_id="camp_001",
            impressions=1000,
            spend_cents=10000,
        )
    )
    session.add(
        InsightFactory.create(
            date=date(2026, 3, 15),
            level="campaign",
            ad_account_id=account.id,
            entity_id="camp_001",
            impressions=500,
            spend_cents=5000,
        )
    )
    session.add(
        InsightFactory.create(
            date=date(2026, 3, 31),
            level="campaign",
            ad_account_id=account.id,
            entity_id="camp_001",
            impressions=250,
            spend_cents=2500,
        )
    )
    session.commit()

    report = ReportService().get_dashboard_data_for_accounts(
        [account.id],
        date(2026, 4, 1),
        date(2026, 4, 30),
        date(2026, 3, 1),
        date(2026, 3, 31),
    )

    assert report.summary.impressions == 1000
    assert report.prev_summary.impressions == 750
    assert report.prev_summary.spend_cents == 7500


def test_prev_period_calculation():
    svc = ReportService()
    date_from = date(2024, 1, 8)
    date_to = date(2024, 1, 14)
    prev_from, prev_to = svc._prev_period(date_from, date_to)
    assert prev_from == date(2024, 1, 1)
    assert prev_to == date(2024, 1, 7)
