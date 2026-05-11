"""factory_boy factories for test data creation."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import factory
from werkzeug.security import generate_password_hash

from adsreport.db.models.ad_account import AdAccount
from adsreport.db.models.campaign import Campaign
from adsreport.db.models.insight import Insight
from adsreport.db.models.sync_run import SyncRun
from adsreport.db.models.user import User


def _uuid() -> str:
    return str(uuid.uuid4())


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(_uuid)
    username = factory.Sequence(lambda n: f"user_{n}")
    password_hash = factory.LazyFunction(lambda: generate_password_hash("testpassword123"))
    is_active = True
    preferred_locale = "pt-BR"
    created_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))


class AdAccountFactory(factory.Factory):
    class Meta:
        model = AdAccount

    id = factory.LazyFunction(_uuid)
    fb_account_id = factory.Sequence(lambda n: f"act_{n:012d}")
    name = factory.Sequence(lambda n: f"Test Account {n}")
    currency = "BRL"
    timezone = "America/Sao_Paulo"
    status = "active"
    is_default = False
    created_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))


class CampaignFactory(factory.Factory):
    class Meta:
        model = Campaign

    id = factory.LazyFunction(_uuid)
    fb_campaign_id = factory.Sequence(lambda n: f"camp_{n:012d}")
    ad_account_id = factory.LazyFunction(_uuid)
    name = factory.Sequence(lambda n: f"Test Campaign {n}")
    objective = "OUTCOME_LEADS"
    status = "ACTIVE"
    effective_status = "ACTIVE"
    created_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))


class InsightFactory(factory.Factory):
    class Meta:
        model = Insight

    id = factory.LazyFunction(_uuid)
    date = factory.LazyFunction(lambda: date.today())
    level = "campaign"
    entity_id = factory.LazyFunction(_uuid)
    ad_account_id = factory.LazyFunction(_uuid)
    impressions = factory.Faker("random_int", min=1000, max=100000)
    clicks = factory.Faker("random_int", min=10, max=5000)
    spend_cents = factory.Faker("random_int", min=1000, max=500000)
    reach = factory.Faker("random_int", min=500, max=80000)
    frequency = factory.Faker("pyfloat", min_value=1.0, max_value=5.0)
    ctr = factory.Faker("pyfloat", min_value=0.1, max_value=10.0)
    cpc_cents = factory.Faker("random_int", min=50, max=5000)
    cpm_cents = factory.Faker("random_int", min=500, max=20000)
    conversions = factory.Faker("random_int", min=0, max=100)
    leads = factory.Faker("random_int", min=0, max=50)
    purchase_value_cents = factory.Faker("random_int", min=0, max=1000000)
    roas = factory.Faker("pyfloat", min_value=0.0, max_value=10.0)
    synced_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))
