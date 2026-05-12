from __future__ import annotations

from typing import TYPE_CHECKING

from dash import Input, Output, State, callback

from adsreport.core.time import date_range
from adsreport.db.session import session_scope
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.repositories.insight_repo import InsightRepository
from adsreport.ui.components.filter_bar import _account_options

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@callback(
    Output("filter-account", "options"),
    Output("filter-account", "value"),
    Input("filter-account-options-poll", "n_intervals"),
    Input("filter-refresh-btn", "n_clicks"),
    State("filter-account", "value"),
)
def refresh_account_filter_options(
    _poll: int | None,
    _refresh_clicks: int | None,
    selected_account_ids: list[str] | None,
) -> tuple[list[dict[str, str]], list[str] | None]:
    options = _account_options()
    valid_values = {option["value"] for option in options}
    selected = [
        account_id
        for account_id in selected_account_ids or []
        if account_id in valid_values
    ]
    return options, selected or None


@callback(
    Output("filter-campaign", "options"),
    Output("filter-campaign", "value"),
    Input("filter-period", "value"),
    Input("filter-account", "value"),
    Input("filter-refresh-btn", "n_clicks"),
    State("filter-campaign", "value"),
)
def refresh_campaign_filter_options(
    period: str | None,
    selected_account_ids: list[str] | str | None,
    _refresh_clicks: int | None,
    selected_campaign_ids: list[str] | None,
) -> tuple[list[dict[str, str]], list[str] | None]:
    date_from, date_to = date_range(period or "last_7_days")

    with session_scope() as session:
        account_ids = _selected_or_default_account_ids(session, selected_account_ids)
        options = InsightRepository(session).get_delivered_campaign_options(
            account_ids,
            date_from,
            date_to,
        )

    valid_values = {option["value"] for option in options}
    selected = [
        campaign_id
        for campaign_id in selected_campaign_ids or []
        if campaign_id in valid_values
    ]
    return options, selected or None


def _selected_or_default_account_ids(
    session: Session,
    selected_account_ids: list[str] | str | None,
) -> list[str]:
    account_repo = AdAccountRepository(session)
    selected_ids = _normalize_ids(selected_account_ids)
    if selected_ids:
        return [
            account.id
            for account_id in selected_ids
            if (account := account_repo.get_by_id(account_id)) is not None
        ]

    default = account_repo.get_default()
    if default is not None:
        return [default.id]
    return [account.id for account in account_repo.get_all_active()]


def _normalize_ids(ids: list[str] | str | None) -> list[str]:
    if ids is None:
        return []
    if isinstance(ids, str):
        return [ids]
    return [item for item in ids if item]
