"""Integration test for the sync flow with a mocked Facebook client."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from adsreport.constants import SyncStatus
from adsreport.services.ads_sync_service import AdsSyncService
from tests.factories import AdAccountFactory


def _mock_fb_client() -> MagicMock:
    client = MagicMock()
    client.get_insights.return_value = [
        {
            "date_start": "2024-01-01",
            "campaign_id": "camp_001",
            "campaign_name": "Leads Campaign",
            "adset_id": "adset_001",
            "adset_name": "Prospecting Ad Set",
            "impressions": "5000",
            "clicks": "150",
            "spend": "75.50",
            "reach": "4000",
            "frequency": "1.25",
            "ctr": "3.0",
            "cpc": "0.50",
            "cpm": "15.10",
            "actions": [{"action_type": "lead", "value": "10"}],
            "action_values": [],
        }
    ]
    return client


def test_sync_account_success(session):
    account = AdAccountFactory.create(fb_account_id="act_123456")
    session.add(account)
    session.commit()

    fb = _mock_fb_client()
    svc = AdsSyncService(fb)
    run = svc.sync_account(account.id, date(2024, 1, 1), date(2024, 1, 1))

    assert run.status == SyncStatus.SUCCESS
    assert run.records_upserted > 0
    fb.get_insights.assert_called()

    from sqlalchemy import select

    from adsreport.db.models.adset import AdSet
    from adsreport.db.models.campaign import Campaign

    campaign = session.scalar(select(Campaign).where(Campaign.fb_campaign_id == "camp_001"))
    adset = session.scalar(select(AdSet).where(AdSet.fb_adset_id == "adset_001"))
    assert campaign is not None
    assert campaign.name == "Leads Campaign"
    assert adset is not None
    assert adset.name == "Prospecting Ad Set"


def test_sync_all_accounts_syncs_each_active_account(session):
    account_one = AdAccountFactory.create(fb_account_id="act_111", sync_enabled=True)
    account_two = AdAccountFactory.create(fb_account_id="act_222", sync_enabled=True)
    disabled = AdAccountFactory.create(fb_account_id="act_333", status="disabled", sync_enabled=False)
    session.add_all([account_one, account_two, disabled])
    session.commit()

    fb = _mock_fb_client()
    svc = AdsSyncService(fb)
    runs = svc.sync_all_accounts(date(2024, 1, 1), date(2024, 1, 1))

    assert len(runs) == 2
    assert {run.ad_account_id for run in runs} == {account_one.id, account_two.id}
    assert fb.get_insights.call_count == 6

    from sqlalchemy import func, select

    from adsreport.db.models.insight import Insight

    synced_accounts = session.scalars(select(Insight.ad_account_id).distinct()).all()
    insight_count = session.scalar(select(func.count()).select_from(Insight))
    assert set(synced_accounts) == {account_one.id, account_two.id}
    assert insight_count == 6


def test_sync_upsert_is_idempotent(session):
    account = AdAccountFactory.create(fb_account_id="act_789")
    session.add(account)
    session.commit()

    fb = _mock_fb_client()
    svc = AdsSyncService(fb)

    run1 = svc.sync_account(account.id, date(2024, 1, 1), date(2024, 1, 1))
    run2 = svc.sync_account(account.id, date(2024, 1, 1), date(2024, 1, 1))

    assert run1.status == SyncStatus.SUCCESS
    assert run2.status == SyncStatus.SUCCESS

    from sqlalchemy import func, select

    from adsreport.db.models.insight import Insight

    insight_count = session.scalar(
        select(func.count()).select_from(Insight).where(Insight.ad_account_id == account.id)
    )
    assert insight_count == run1.records_upserted
