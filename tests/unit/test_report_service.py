from __future__ import annotations

from datetime import date, timedelta

import pytest

from adsreport.services.report_service import ReportService
from tests.factories import AdAccountFactory, InsightFactory


def _seed_insights(session, account_id: str, days: int = 7) -> None:
    from adsreport.db.models.insight import Insight

    today = date.today()
    for i in range(days):
        insight = InsightFactory.create(
            date=today - timedelta(days=i),
            level="campaign",
            ad_account_id=account_id,
            entity_id="camp_001",
            impressions=1000,
            clicks=50,
            spend_cents=5000,
            leads=5,
            conversions=2,
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
    session.add(account)
    session.commit()
    _seed_insights(session, account.id, days=7)

    report = ReportService().get_dashboard_data(
        account.id,
        date.today() - timedelta(days=6),
        date.today(),
    )
    assert report.has_data
    assert report.summary.impressions == 7000
    assert report.summary.spend_cents == 35000
    assert len(report.time_series) == 7
    assert len(report.top_campaigns) == 1


def test_prev_period_calculation():
    svc = ReportService()
    date_from = date(2024, 1, 8)
    date_to = date(2024, 1, 14)
    prev_from, prev_to = svc._prev_period(date_from, date_to)
    assert prev_from == date(2024, 1, 1)
    assert prev_to == date(2024, 1, 7)
