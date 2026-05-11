from __future__ import annotations

from datetime import UTC, date, datetime

from adsreport.db.models.insight import Insight
from adsreport.repositories.insight_repo import InsightRepository
from tests.factories import AdAccountFactory


def test_upsert_updates_existing_insight_without_duplicate(session):
    account = AdAccountFactory.create()
    session.add(account)
    session.commit()

    repo = InsightRepository(session)
    first = Insight(
        date=date(2024, 1, 1),
        level="campaign",
        entity_id="campaign-1",
        ad_account_id=account.id,
        impressions=100,
        clicks=10,
        spend_cents=2500,
        reach=80,
        frequency=1.25,
        ctr=10.0,
        cpc_cents=250,
        cpm_cents=25000,
        conversions=1,
        leads=1,
        purchase_value_cents=0,
        roas=0.0,
        synced_at=datetime.now(tz=UTC),
    )
    saved = repo.upsert(first)

    replacement = Insight(
        date=date(2024, 1, 1),
        level="campaign",
        entity_id="campaign-1",
        ad_account_id=account.id,
        impressions=200,
        clicks=20,
        spend_cents=5000,
        reach=150,
        frequency=1.33,
        ctr=10.0,
        cpc_cents=250,
        cpm_cents=25000,
        conversions=2,
        leads=2,
        purchase_value_cents=0,
        roas=0.0,
        synced_at=datetime.now(tz=UTC),
    )
    updated = repo.upsert(replacement)

    rows = repo.get_by_account_range(account.id, date(2024, 1, 1), date(2024, 1, 1))
    assert updated.id == saved.id
    assert len(rows) == 1
    assert rows[0].impressions == 200
    assert rows[0].spend_cents == 5000
