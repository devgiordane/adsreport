from __future__ import annotations

import logging

import plotly.graph_objects as go
from dash import Input, Output, State, callback, clientside_callback, html, no_update

from adsreport.core.time import (
    comparison_date_range,
    date_range,
    format_currency,
    format_number,
    format_percent,
)
from adsreport.db.session import session_scope
from adsreport.i18n import t
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.services.report_service import ReportService
from adsreport.services.scheduler_service import SchedulerService
from adsreport.ui.components.chart_block import chart_block
from adsreport.ui.components.data_table import data_table
from adsreport.ui.components.empty_state import empty_state
from adsreport.ui.components.kpi_card import kpi_card
from adsreport.ui.theme import plotly_template

_log = logging.getLogger(__name__)

clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            window.setTimeout(function() { window.print(); }, 50);
        }
        return n_clicks || 0;
    }
    """,
    Output("dashboard-print-store", "data"),
    Input("dashboard-export-pdf-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("dashboard-kpi-grid", "children"),
    Output("dashboard-timeseries", "children"),
    Output("dashboard-breakdown", "children"),
    Output("dashboard-top-campaigns", "children"),
    Input("filter-period", "value"),
    Input("filter-account", "value"),
    Input("filter-campaign", "value"),
    Input("dashboard-poll", "n_intervals"),
)
def update_dashboard(
    period: str | None,
    account_ids: list[str] | None,
    campaign_ids: list[str] | str | None,
    _poll: int,
) -> tuple[object, object, object, object]:
    period = period or "last_7_days"

    try:
        with session_scope() as session:
            repo = AdAccountRepository(session)
            accounts = _select_accounts(_normalize_ids(account_ids), repo)

            if not accounts:
                return _empty_dashboard()

            date_from, date_to = date_range(period)
            prev_date_from, prev_date_to = comparison_date_range(period, date_from, date_to)
            report = ReportService(session).get_dashboard_data_for_accounts(
                [account.id for account in accounts],
                date_from,
                date_to,
                prev_date_from,
                prev_date_to,
                _normalize_ids(campaign_ids),
            )
    except Exception:
        _log.exception("Failed to load dashboard data")
        return _empty_dashboard()

    if not report.has_data:
        return _empty_dashboard()

    currency = _resolve_currency([account.currency for account in accounts])
    template = plotly_template()

    return (
        _kpi_cards(report.summary, report.prev_summary, currency),
        _leads_timeseries_block(report.time_series, template),
        _build_breakdown_block(report.top_campaigns, template),
        _build_campaign_tables(report, currency),
    )


@callback(
    Output("dashboard-sync-msg", "children"),
    Input("dashboard-sync-btn", "n_clicks"),
    State("filter-account", "value"),
    prevent_initial_call=True,
)
def trigger_dashboard_sync(
    n_clicks: int | None,
    account_ids: list[str] | str | None,
) -> object:
    if not n_clicks:
        return no_update

    selected = _normalize_ids(account_ids)
    try:
        SchedulerService().trigger_sync_now(
            triggered_by="manual",
            account_ids=selected or None,
        )
    except Exception:
        _log.exception("Failed to trigger sync")
        return html.Span(
            t("sync.error"),
            style={"color": "var(--danger)", "fontWeight": "600"},
        )
    return html.Span(
        t("sync.triggered"),
        style={"color": "var(--success)", "fontWeight": "600"},
    )


def _select_accounts(account_ids: list[str], repo: AdAccountRepository) -> list[object]:
    if account_ids:
        return [a for a in (repo.get_by_id(aid) for aid in account_ids) if a is not None]
    default = repo.get_default()
    return [default] if default else repo.get_all_active()


def _empty_dashboard() -> tuple[object, object, object, object]:
    return [], empty_state("no_data", on_cta_id="dashboard-sync-btn"), html.Div(), html.Div()


def _kpi_cards(s: object, p: object, currency: str = "BRL") -> list[html.Div]:
    def delta(curr: float, prev: float) -> float | None:
        if prev == 0:
            return None
        return (curr - prev) / prev * 100

    cards = [
        kpi_card("impressions", format_number(s.impressions), delta(s.impressions, p.impressions)),
        kpi_card("clicks", format_number(s.clicks), delta(s.clicks, p.clicks)),
        kpi_card("ctr", format_percent(s.ctr), delta(s.ctr, p.ctr)),
        kpi_card("cpc", format_currency(s.cpc_cents, currency), delta(s.cpc_cents, p.cpc_cents)),
        kpi_card("cpm", format_currency(s.cpm_cents, currency), delta(s.cpm_cents, p.cpm_cents)),
        kpi_card("spend", format_currency(s.spend_cents, currency), delta(s.spend_cents, p.spend_cents)),
        kpi_card("leads", format_number(s.leads), delta(s.leads, p.leads)),
        kpi_card(
            "cost_per_lead",
            format_currency(s.cost_per_lead_cents, currency),
            delta(s.cost_per_lead_cents, p.cost_per_lead_cents),
        ),
    ]
    if s.has_roas:
        cards.append(kpi_card("roas", f"{s.roas:.2f}x", delta(s.roas, p.roas)))
    return cards


def _leads_timeseries_block(time_series: list[object], template: dict[str, object]) -> html.Div:
    dates = [str(pt.date) for pt in time_series]
    fig = go.Figure(
        [
            go.Scatter(
                x=dates,
                y=[pt.leads for pt in time_series],
                name=t("dashboard.chart.timeseries.leads_legend"),
                mode="lines+markers+text",
                text=[format_number(pt.leads) for pt in time_series],
                textposition="top center",
                hovertemplate="%{x}<br>%{fullData.name}: %{y}<extra></extra>",
            ),
        ]
    )
    fig.update_layout(
        **template["layout"],
        showlegend=True,
        xaxis_title=t("dashboard.chart.timeseries.xaxis"),
        yaxis_title=t("dashboard.chart.timeseries.yaxis"),
    )
    fig.update_yaxes(rangemode="tozero", tickformat=",d")
    return chart_block(t("dashboard.chart.timeseries.title"), fig, "dashboard-timeseries-graph")


def _build_breakdown_block(top_campaigns: list[object], template: dict[str, object]) -> html.Div:
    campaigns = top_campaigns[:8]
    fig = go.Figure(
        go.Bar(
            x=[c.name for c in campaigns],
            y=[c.spend_cents / 100 for c in campaigns],
            name=t("dashboard.kpi.spend"),
        )
    )
    fig.update_layout(**template["layout"])
    return chart_block(t("dashboard.chart.breakdown.title"), fig, "dashboard-breakdown-graph")


def _build_campaign_tables(report: object, currency: str) -> html.Div:
    s = report.summary
    base_columns = [
        {"name": t("dashboard.table.spend"), "id": "spend"},
        {"name": t("dashboard.table.impressions"), "id": "impressions"},
        {"name": t("dashboard.table.clicks"), "id": "clicks"},
        {"name": t("dashboard.table.ctr"), "id": "ctr"},
        {"name": t("dashboard.table.leads"), "id": "leads"},
        {"name": t("dashboard.table.cost_per_lead"), "id": "cost_per_lead"},
    ]
    if s.has_roas:
        base_columns.append({"name": t("dashboard.table.roas"), "id": "roas"})

    campaign_columns = [{"name": t("dashboard.table.campaign"), "id": "entity_id"}, *base_columns]
    tables = [
        data_table(
            "dashboard-campaigns-table",
            campaign_columns,
            _entity_rows(report.top_campaigns, currency),
            t("dashboard.table.top_campaigns"),
        )
    ]

    if report.top_adsets:
        adset_columns = [{"name": t("dashboard.table.adset"), "id": "entity_id"}, *base_columns]
        tables.append(
            data_table(
                "dashboard-adsets-table",
                adset_columns,
                _entity_rows(report.top_adsets, currency),
                t("dashboard.table.top_adsets"),
            )
        )

    return html.Div(tables, style={"display": "flex", "flexDirection": "column", "gap": "16px"})


def _entity_rows(rows: list[object], currency: str = "BRL") -> list[dict[str, str]]:
    return [
        {
            "entity_id": row.name,
            "spend": format_currency(row.spend_cents, currency),
            "impressions": format_number(row.impressions),
            "clicks": format_number(row.clicks),
            "ctr": format_percent(row.ctr),
            "roas": f"{row.roas:.2f}x",
            "leads": format_number(row.leads),
            "cost_per_lead": format_currency(row.cost_per_lead_cents, currency),
        }
        for row in rows
    ]


def _resolve_currency(currencies: list[str]) -> str:
    unique = {currency for currency in currencies if currency}
    if len(unique) == 1:
        return unique.pop()
    if not unique:
        return "BRL"
    return "MIXED"


def _normalize_ids(ids: list[str] | str | None) -> list[str]:
    if ids is None:
        return []
    if isinstance(ids, str):
        return [ids]
    return [item for item in ids if item]
