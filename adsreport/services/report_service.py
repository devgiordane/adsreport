"""Report aggregations: transforms raw insight rows into dashboard-ready structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from adsreport.repositories.adset_repo import AdSetRepository
from adsreport.repositories.campaign_repo import CampaignRepository
from adsreport.repositories.insight_repo import InsightRepository

if TYPE_CHECKING:
    from datetime import date

    from sqlalchemy.orm import Session

    from adsreport.db.models.insight import Insight


@dataclass
class KPISummary:
    impressions: int = 0
    clicks: int = 0
    spend_cents: int = 0
    reach: int = 0
    leads: int = 0
    conversions: int = 0
    purchase_value_cents: int = 0
    ctr: float = 0.0
    cpc_cents: int = 0
    cpm_cents: int = 0
    roas: float = 0.0

    @property
    def spend(self) -> float:
        return self.spend_cents / 100

    @property
    def cpc(self) -> float:
        return self.cpc_cents / 100

    @property
    def cpm(self) -> float:
        return self.cpm_cents / 100

    @property
    def cost_per_lead_cents(self) -> int:
        if not self.leads:
            return 0
        return round(self.spend_cents / self.leads)

    @property
    def has_roas(self) -> bool:
        return self.purchase_value_cents > 0 and self.spend_cents > 0

    @property
    def purchase_value(self) -> float:
        return self.purchase_value_cents / 100


@dataclass
class TimeSeriesPoint:
    date: date
    impressions: int
    clicks: int
    spend_cents: int
    leads: int
    conversions: int


@dataclass
class CampaignRow:
    entity_id: str
    name: str
    impressions: int
    clicks: int
    spend_cents: int
    ctr: float
    roas: float
    leads: int

    @property
    def cost_per_lead_cents(self) -> int:
        if not self.leads:
            return 0
        return round(self.spend_cents / self.leads)


@dataclass
class ReportData:
    summary: KPISummary = field(default_factory=KPISummary)
    prev_summary: KPISummary = field(default_factory=KPISummary)
    time_series: list[TimeSeriesPoint] = field(default_factory=list)
    top_campaigns: list[CampaignRow] = field(default_factory=list)
    top_adsets: list[CampaignRow] = field(default_factory=list)
    has_data: bool = False


class ReportService:
    def __init__(self, session: Session | None = None) -> None:
        self._insights = InsightRepository(session)
        self._campaigns = CampaignRepository(self._insights.session)
        self._adsets = AdSetRepository(self._insights.session)

    def close(self) -> None:
        self._insights.close()

    def __enter__(self) -> ReportService:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def get_dashboard_data(
        self,
        ad_account_id: str,
        date_from: date,
        date_to: date,
        prev_date_from: date | None = None,
        prev_date_to: date | None = None,
        campaign_ids: list[str] | None = None,
    ) -> ReportData:
        return self.get_dashboard_data_for_accounts(
            [ad_account_id],
            date_from,
            date_to,
            prev_date_from,
            prev_date_to,
            campaign_ids,
        )

    def get_dashboard_data_for_accounts(
        self,
        ad_account_ids: list[str],
        date_from: date,
        date_to: date,
        prev_date_from: date | None = None,
        prev_date_to: date | None = None,
        campaign_ids: list[str] | None = None,
    ) -> ReportData:
        insights = self._insights.get_by_accounts_range(
            ad_account_ids,
            date_from,
            date_to,
            level="campaign",
            entity_ids=campaign_ids,
        )

        if not insights:
            return ReportData(has_data=False)

        summary = self._aggregate(insights)
        time_series = self._build_time_series(insights)
        top_campaigns = self._top_campaigns(insights)
        adset_insights = self._insights.get_by_accounts_range(
            ad_account_ids,
            date_from,
            date_to,
            level="adset",
        )
        top_adsets = self._top_adsets(adset_insights)

        prev_from, prev_to = (
            (prev_date_from, prev_date_to)
            if prev_date_from is not None and prev_date_to is not None
            else self._prev_period(date_from, date_to)
        )
        prev_insights = self._insights.get_by_accounts_range(
            ad_account_ids,
            prev_from,
            prev_to,
            level="campaign",
            entity_ids=campaign_ids,
        )
        prev_summary = self._aggregate(prev_insights)

        return ReportData(
            summary=summary,
            prev_summary=prev_summary,
            time_series=time_series,
            top_campaigns=top_campaigns,
            top_adsets=top_adsets,
            has_data=True,
        )

    def _aggregate(self, insights: list[Insight]) -> KPISummary:
        s = KPISummary()
        for i in insights:
            s.impressions += i.impressions
            s.clicks += i.clicks
            s.spend_cents += i.spend_cents
            s.reach += i.reach
            s.leads += i.leads
            s.conversions += i.conversions
            s.purchase_value_cents += i.purchase_value_cents
        if s.impressions:
            s.ctr = s.clicks / s.impressions * 100
            s.cpm_cents = round(s.spend_cents / s.impressions * 1000)
        if s.clicks:
            s.cpc_cents = round(s.spend_cents / s.clicks)
        if s.spend_cents:
            s.roas = s.purchase_value_cents / s.spend_cents
        return s

    def _build_time_series(self, insights: list[Insight]) -> list[TimeSeriesPoint]:
        by_date: dict[date, TimeSeriesPoint] = {}
        for i in insights:
            dt = i.date
            if dt not in by_date:
                by_date[dt] = TimeSeriesPoint(date=dt, impressions=0, clicks=0, spend_cents=0, leads=0, conversions=0)
            p = by_date[dt]
            p.impressions += i.impressions
            p.clicks += i.clicks
            p.spend_cents += i.spend_cents
            p.leads += i.leads
            p.conversions += i.conversions
        return sorted(by_date.values(), key=lambda x: x.date)

    def _top_campaigns(self, insights: list[Insight], limit: int = 10) -> list[CampaignRow]:
        names = self._campaigns.get_names_by_fb_ids(list({i.entity_id for i in insights}))
        return self._top_entities(insights, names, limit)

    def _top_adsets(self, insights: list[Insight], limit: int = 10) -> list[CampaignRow]:
        names = self._adsets.get_names_by_fb_ids(list({i.entity_id for i in insights}))
        return self._top_entities(insights, names, limit)

    def _top_entities(
        self,
        insights: list[Insight],
        names: dict[str, str],
        limit: int = 10,
    ) -> list[CampaignRow]:
        by_campaign: dict[str, CampaignRow] = {}
        for i in insights:
            eid = i.entity_id
            if eid not in by_campaign:
                by_campaign[eid] = CampaignRow(
                    entity_id=eid,
                    name=names.get(eid, eid),
                    impressions=0,
                    clicks=0,
                    spend_cents=0,
                    ctr=0.0,
                    roas=0.0,
                    leads=0,
                )
            r = by_campaign[eid]
            r.impressions += i.impressions
            r.clicks += i.clicks
            r.spend_cents += i.spend_cents
            r.leads += i.leads
        for r in by_campaign.values():
            if r.impressions:
                r.ctr = r.clicks / r.impressions * 100
        sorted_rows = sorted(by_campaign.values(), key=lambda x: x.spend_cents, reverse=True)
        return sorted_rows[:limit]

    def get_campaign_rows(
        self,
        ad_account_ids: list[str],
        date_from: date,
        date_to: date,
        campaign_ids: list[str] | None = None,
        limit: int = 100,
    ) -> tuple[KPISummary, list[CampaignRow]]:
        insights = self._insights.get_by_accounts_range(
            ad_account_ids, date_from, date_to, level="campaign", entity_ids=campaign_ids
        )
        if not insights:
            return KPISummary(), []
        return self._aggregate(insights), self._top_campaigns(insights, limit=limit)

    def get_campaign_timeseries(
        self,
        ad_account_ids: list[str],
        date_from: date,
        date_to: date,
        entity_id: str,
    ) -> list[TimeSeriesPoint]:
        insights = self._insights.get_by_accounts_range(
            ad_account_ids, date_from, date_to, level="campaign", entity_ids=[entity_id]
        )
        return self._build_time_series(insights)

    def _prev_period(self, date_from: date, date_to: date) -> tuple[date, date]:
        from datetime import timedelta

        delta = (date_to - date_from).days + 1
        return date_from - timedelta(days=delta), date_from - timedelta(days=1)
