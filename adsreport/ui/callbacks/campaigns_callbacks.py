from __future__ import annotations

import logging

import plotly.graph_objects as go
from dash import Input, Output, State, callback, html, no_update

from adsreport.core.time import date_range, format_currency, format_number, format_percent
from adsreport.db.session import session_scope
from adsreport.i18n import t
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.repositories.campaign_repo import CampaignRepository
from adsreport.services.report_service import ReportService
from adsreport.ui.callbacks.dashboard_callbacks import _normalize_ids, _resolve_currency, _select_accounts
from adsreport.ui.components.chart_block import chart_block
from adsreport.ui.components.empty_state import empty_state
from adsreport.ui.theme import plotly_template

_log = logging.getLogger(__name__)

_HIDDEN = {"display": "none"}
_VISIBLE = {"display": "block"}


@callback(
    Output("campaigns-table", "data"),
    Output("campaigns-table", "columns"),
    Output("campaigns-table-container", "style"),
    Output("campaigns-table-msg", "children"),
    Input("filter-period", "value"),
    Input("filter-account", "value"),
    Input("filter-campaign", "value"),
    Input("campaigns-poll", "n_intervals"),
)
def update_campaigns_table(
    period: str | None,
    account_ids: list[str] | None,
    campaign_ids: list[str] | str | None,
    _poll: int,
) -> tuple[list, list, dict, object]:
    period = period or "last_7_days"

    try:
        with session_scope() as session:
            repo = AdAccountRepository(session)
            accounts = _select_accounts(_normalize_ids(account_ids), repo)

            if not accounts:
                return [], [], _HIDDEN, empty_state("no_data", on_cta_id="dashboard-sync-btn")

            date_from, date_to = date_range(period)
            campaign_filter = _normalize_ids(campaign_ids) or None

            campaign_meta: dict[str, object] = {}
            for account in accounts:
                for c in CampaignRepository(session).get_by_account(account.id):
                    campaign_meta[c.fb_campaign_id] = c

            summary, rows = ReportService(session).get_campaign_rows(
                [a.id for a in accounts],
                date_from,
                date_to,
                campaign_filter,
            )
    except Exception:
        _log.exception("Failed to load campaigns table")
        return [], [], _HIDDEN, empty_state("no_data", on_cta_id="dashboard-sync-btn")

    if not rows:
        return [], [], _HIDDEN, empty_state("no_data", on_cta_id="dashboard-sync-btn")

    currency = _resolve_currency([a.currency for a in accounts])
    return (
        _campaign_rows(rows, campaign_meta, currency),
        _campaign_columns(summary.has_roas),
        _VISIBLE,
        None,
    )


@callback(
    Output("campaigns-drill-chart", "children"),
    Input("campaigns-table", "active_cell"),
    State("campaigns-table", "derived_virtual_data"),
    State("filter-period", "value"),
    State("filter-account", "value"),
    prevent_initial_call=True,
)
def update_campaign_drill(
    active_cell: dict | None,
    visible_rows: list[dict] | None,
    period: str | None,
    account_ids: list[str] | None,
) -> object:
    if not active_cell or not visible_rows:
        return no_update

    row_index = active_cell.get("row")
    if not isinstance(row_index, int) or row_index >= len(visible_rows):
        return no_update

    entity_id = visible_rows[row_index].get("entity_id")
    name = visible_rows[row_index].get("name", entity_id)
    if not entity_id:
        return no_update

    period = period or "last_7_days"
    try:
        with session_scope() as session:
            accounts = _select_accounts(_normalize_ids(account_ids), AdAccountRepository(session))
            if not accounts:
                return html.Div()
            date_from, date_to = date_range(period)
            timeseries = ReportService(session).get_campaign_timeseries(
                [a.id for a in accounts], date_from, date_to, entity_id
            )
    except Exception:
        _log.exception("Failed to load campaign drill chart")
        return html.Div()

    if not timeseries:
        return html.Div()

    template = plotly_template()
    fig = go.Figure(
        [
            go.Scatter(
                x=[str(pt.date) for pt in timeseries],
                y=[pt.leads for pt in timeseries],
                name=t("dashboard.chart.timeseries.leads_legend"),
                mode="lines+markers+text",
                text=[format_number(pt.leads) for pt in timeseries],
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
    return chart_block(t("campaigns.drill.title", name=name), fig, "campaigns-drill-graph")


def _campaign_columns(has_roas: bool) -> list[dict]:
    cols = [
        {"name": "", "id": "entity_id"},
        {"name": t("campaigns.table.name"), "id": "name"},
        {"name": t("campaigns.table.status"), "id": "status"},
        {"name": t("campaigns.table.objective"), "id": "objective"},
        {"name": t("campaigns.table.spend"), "id": "spend"},
        {"name": t("campaigns.table.impressions"), "id": "impressions"},
        {"name": t("campaigns.table.clicks"), "id": "clicks"},
        {"name": t("campaigns.table.ctr"), "id": "ctr"},
        {"name": t("campaigns.table.leads"), "id": "leads"},
    ]
    if has_roas:
        cols.append({"name": t("campaigns.table.roas"), "id": "roas"})
    return cols


def _campaign_rows(
    rows: list[object],
    meta: dict[str, object],
    currency: str = "BRL",
) -> list[dict]:
    result = []
    for row in rows:
        campaign = meta.get(row.entity_id)
        result.append({
            "entity_id": row.entity_id,
            "name": row.name,
            "status": _format_status(campaign.effective_status if campaign else ""),
            "objective": _format_objective(campaign.objective if campaign else ""),
            "spend": format_currency(row.spend_cents, currency),
            "impressions": format_number(row.impressions),
            "clicks": format_number(row.clicks),
            "ctr": format_percent(row.ctr),
            "leads": format_number(row.leads),
            "roas": f"{row.roas:.2f}x",
        })
    return result


def _format_objective(objective: str) -> str:
    return objective.replace("OUTCOME_", "").replace("_", " ").title()


def _format_status(status: str) -> str:
    return status.replace("_", " ").title()
