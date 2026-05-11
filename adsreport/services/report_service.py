"""Report aggregations: transforms raw insight rows into dashboard-ready structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from adsreport.repositories.insight_repo import InsightRepository


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


@dataclass
class ReportData:
    summary: KPISummary = field(default_factory=KPISummary)
    prev_summary: KPISummary = field(default_factory=KPISummary)
    time_series: list[TimeSeriesPoint] = field(default_factory=list)
    top_campaigns: list[CampaignRow] = field(default_factory=list)
    has_data: bool = False


class ReportService:
    def __init__(self) -> None:
        self._insights = InsightRepository()

    def get_dashboard_data(
        self,
        ad_account_id: str,
        date_from: date,
        date_to: date,
    ) -> ReportData:
        insights = self._insights.get_by_account_range(ad_account_id, date_from, date_to, level="campaign")

        if not insights:
            return ReportData(has_data=False)

        summary = self._aggregate(insights)
        time_series = self._build_time_series(insights)
        top_campaigns = self._top_campaigns(insights)

        prev_from, prev_to = self._prev_period(date_from, date_to)
        prev_insights = self._insights.get_by_account_range(ad_account_id, prev_from, prev_to, level="campaign")
        prev_summary = self._aggregate(prev_insights)

        return ReportData(
            summary=summary,
            prev_summary=prev_summary,
            time_series=time_series,
            top_campaigns=top_campaigns,
            has_data=True,
        )

    def _aggregate(self, insights: list[object]) -> KPISummary:
        s = KPISummary()
        for i in insights:
            s.impressions += i.impressions  # type: ignore[union-attr]
            s.clicks += i.clicks  # type: ignore[union-attr]
            s.spend_cents += i.spend_cents  # type: ignore[union-attr]
            s.reach += i.reach  # type: ignore[union-attr]
            s.leads += i.leads  # type: ignore[union-attr]
            s.conversions += i.conversions  # type: ignore[union-attr]
            s.purchase_value_cents += i.purchase_value_cents  # type: ignore[union-attr]
        if s.impressions:
            s.ctr = s.clicks / s.impressions * 100
            s.cpm_cents = round(s.spend_cents / s.impressions * 1000)
        if s.clicks:
            s.cpc_cents = round(s.spend_cents / s.clicks)
        if s.spend_cents:
            s.roas = s.purchase_value_cents / s.spend_cents
        return s

    def _build_time_series(self, insights: list[object]) -> list[TimeSeriesPoint]:
        by_date: dict[date, TimeSeriesPoint] = {}
        for i in insights:
            dt = i.date  # type: ignore[union-attr]
            if dt not in by_date:
                by_date[dt] = TimeSeriesPoint(date=dt, impressions=0, clicks=0, spend_cents=0, leads=0, conversions=0)
            p = by_date[dt]
            p.impressions += i.impressions  # type: ignore[union-attr]
            p.clicks += i.clicks  # type: ignore[union-attr]
            p.spend_cents += i.spend_cents  # type: ignore[union-attr]
            p.leads += i.leads  # type: ignore[union-attr]
            p.conversions += i.conversions  # type: ignore[union-attr]
        return sorted(by_date.values(), key=lambda x: x.date)

    def _top_campaigns(self, insights: list[object], limit: int = 10) -> list[CampaignRow]:
        by_campaign: dict[str, CampaignRow] = {}
        for i in insights:
            eid = i.entity_id  # type: ignore[union-attr]
            if eid not in by_campaign:
                by_campaign[eid] = CampaignRow(entity_id=eid, name=eid, impressions=0, clicks=0, spend_cents=0, ctr=0.0, roas=0.0, leads=0)
            r = by_campaign[eid]
            r.impressions += i.impressions  # type: ignore[union-attr]
            r.clicks += i.clicks  # type: ignore[union-attr]
            r.spend_cents += i.spend_cents  # type: ignore[union-attr]
            r.leads += i.leads  # type: ignore[union-attr]
        for r in by_campaign.values():
            if r.impressions:
                r.ctr = r.clicks / r.impressions * 100
        sorted_rows = sorted(by_campaign.values(), key=lambda x: x.spend_cents, reverse=True)
        return sorted_rows[:limit]

    def _prev_period(self, date_from: date, date_to: date) -> tuple[date, date]:
        from datetime import timedelta

        delta = (date_to - date_from).days + 1
        return date_from - timedelta(days=delta), date_from - timedelta(days=1)
