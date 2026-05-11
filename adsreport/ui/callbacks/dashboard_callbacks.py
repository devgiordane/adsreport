from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State, callback, no_update

from adsreport.core.time import date_range, format_currency, format_number, format_percent
from adsreport.i18n import t
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.services.report_service import ReportService
from adsreport.ui.components.chart_block import chart_block, empty_figure
from adsreport.ui.components.data_table import data_table
from adsreport.ui.components.empty_state import empty_state
from adsreport.ui.components.kpi_card import kpi_card
from adsreport.ui.theme import plotly_template


@callback(
    Output("dashboard-kpi-grid", "children"),
    Output("dashboard-timeseries", "children"),
    Output("dashboard-breakdown", "children"),
    Output("dashboard-top-campaigns", "children"),
    Input("filter-period", "value"),
    Input("filter-account", "value"),
    Input("dashboard-poll", "n_intervals"),
)
def update_dashboard(
    period: str | None,
    account_ids: list[str] | None,
    _poll: int,
) -> tuple[object, object, object, object]:
    period = period or "last_7_days"

    account_repo = AdAccountRepository()
    if account_ids:
        accounts = [account_repo.get_by_id(aid) for aid in account_ids if account_repo.get_by_id(aid)]
    else:
        default = account_repo.get_default()
        accounts = [default] if default else account_repo.get_all_active()

    if not accounts:
        es = empty_state("no_data", on_cta_id="dashboard-sync-btn")
        return es, es, es, es

    date_from, date_to = date_range(period)
    account_id = accounts[0].id  # type: ignore[union-attr]

    report = ReportService().get_dashboard_data(account_id, date_from, date_to)

    if not report.has_data:
        es = empty_state("no_data", on_cta_id="dashboard-sync-btn")
        return es, es, es, es

    s = report.summary
    p = report.prev_summary

    def delta(curr: float, prev: float) -> float | None:
        if prev == 0:
            return None
        return (curr - prev) / prev * 100

    kpi_cards = [
        kpi_card("impressions", format_number(s.impressions), delta(s.impressions, p.impressions)),
        kpi_card("clicks", format_number(s.clicks), delta(s.clicks, p.clicks)),
        kpi_card("ctr", format_percent(s.ctr), delta(s.ctr, p.ctr)),
        kpi_card("cpc", format_currency(s.cpc_cents), delta(s.cpc_cents, p.cpc_cents)),
        kpi_card("cpm", format_currency(s.cpm_cents), delta(s.cpm_cents, p.cpm_cents)),
        kpi_card("spend", format_currency(s.spend_cents), delta(s.spend_cents, p.spend_cents)),
        kpi_card("leads", format_number(s.leads), delta(s.leads, p.leads)),
        kpi_card("conversions", format_number(s.conversions), delta(s.conversions, p.conversions)),
        kpi_card("roas", f"{s.roas:.2f}x", delta(s.roas, p.roas)),
    ]

    template = plotly_template("dark")

    # Time series
    dates = [str(pt.date) for pt in report.time_series]
    ts_fig = go.Figure(
        [
            go.Scatter(x=dates, y=[pt.spend_cents / 100 for pt in report.time_series],
                       name=t("dashboard.kpi.spend"), mode="lines+markers"),
        ]
    )
    ts_fig.update_layout(**template["layout"])
    ts_block = chart_block(t("dashboard.chart.timeseries.title"), ts_fig, "dashboard-timeseries-graph")

    # Breakdown
    campaigns = report.top_campaigns[:8]
    bd_fig = go.Figure(
        go.Bar(
            x=[c.entity_id for c in campaigns],
            y=[c.spend_cents / 100 for c in campaigns],
        )
    )
    bd_fig.update_layout(**template["layout"])
    bd_block = chart_block(t("dashboard.chart.breakdown.title"), bd_fig, "dashboard-breakdown-graph")

    # Top campaigns table
    columns = [
        {"name": t("dashboard.table.campaign"), "id": "entity_id"},
        {"name": t("dashboard.table.spend"), "id": "spend"},
        {"name": t("dashboard.table.impressions"), "id": "impressions"},
        {"name": t("dashboard.table.clicks"), "id": "clicks"},
        {"name": t("dashboard.table.ctr"), "id": "ctr"},
        {"name": t("dashboard.table.roas"), "id": "roas"},
        {"name": t("dashboard.table.leads"), "id": "leads"},
    ]
    rows = [
        {
            "entity_id": c.entity_id,
            "spend": format_currency(c.spend_cents),
            "impressions": format_number(c.impressions),
            "clicks": format_number(c.clicks),
            "ctr": format_percent(c.ctr),
            "roas": f"{c.roas:.2f}x",
            "leads": format_number(c.leads),
        }
        for c in report.top_campaigns
    ]
    table = data_table("dashboard-campaigns-table", columns, rows, t("dashboard.table.top_campaigns"))

    return kpi_cards, ts_block, bd_block, table
