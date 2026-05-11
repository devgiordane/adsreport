"""Integration test for the sync flow with a mocked Facebook client."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from adsreport.constants import SyncStatus
from adsreport.services.ads_sync_service import AdsSyncService
from tests.factories import AdAccountFactory


def _mock_fb_client() -> MagicMock:
    client = MagicMock()
    client.get_insights.return_value = [
        {
            "date_start": "2024-01-01",
            "campaign_id": "camp_001",
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

    from adsreport.repositories.insight_repo import InsightRepository

    insights = InsightRepository().get_by_account_range(account.id, date(2024, 1, 1), date(2024, 1, 1))
    assert len(insights) == run1.records_upserted
