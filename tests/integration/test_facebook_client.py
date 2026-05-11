"""Facebook client integration tests using VCR.py cassettes.

Real API calls are recorded once and replayed from cassettes in CI.
To record new cassettes: set ADSREPORT_RECORD_VCRECORD=true and provide valid credentials.
"""

from __future__ import annotations

import pytest

# Mark all tests in this module as requiring VCR cassettes
pytestmark = pytest.mark.vcr


@pytest.fixture
def fb_client():
    from adsreport.services.facebook_client import FacebookClient

    return FacebookClient(
        app_id="test_app_id",
        app_secret="test_app_secret",
        access_token="test_access_token",
    )


@pytest.mark.skip(reason="Requires VCR cassettes — run with --record-mode=new_episodes to generate")
def test_get_ad_accounts(fb_client):
    accounts = fb_client.get_ad_accounts()
    assert isinstance(accounts, list)
    for acct in accounts:
        assert "id" in acct
        assert "name" in acct


@pytest.mark.skip(reason="Requires VCR cassettes — run with --record-mode=new_episodes to generate")
def test_get_insights(fb_client):
    insights = fb_client.get_insights("act_123456", "2024-01-01", "2024-01-07")
    assert isinstance(insights, list)
