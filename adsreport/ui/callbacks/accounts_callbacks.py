from dash import Input, Output, State, callback, ctx, html, no_update

from adsreport.db.session import session_scope
from adsreport.i18n import t
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.services.onboarding_service import OnboardingService
from adsreport.services.scheduler_service import SchedulerService
from adsreport.ui.components.accounts_list import accounts_list


@callback(
    Output("accounts-list", "children"),
    Output("accounts-refresh-msg", "children"),
    Input("accounts-refresh-btn", "n_clicks"),
    Input("accounts-poll", "n_intervals"),
)
def render_accounts(refresh_clicks: int | None, _n_intervals: int | None) -> tuple[object, object]:
    if ctx.triggered_id == "accounts-refresh-btn" and refresh_clicks:
        result = OnboardingService().refresh_ad_accounts_from_saved_credentials()
        if result.is_ok():
            accounts = result.unwrap()
            return accounts_list(), html.Span(
                t("accounts.refresh.success", count=len(accounts)),
                style={"color": "var(--success)", "fontWeight": "600"},
            )
        return accounts_list(), html.Span(
            t("accounts.refresh.error", error=result.unwrap_err()),
            style={"color": "var(--danger)"},
        )

    return accounts_list(), no_update


@callback(
    Output("accounts-sync-msg", "children"),
    Input("accounts-table", "active_cell"),
    Input("accounts-sync-selected-btn", "n_clicks"),
    Input("accounts-sync-all-btn", "n_clicks"),
    State("accounts-table", "data"),
    State("accounts-table", "selected_row_ids"),
    State("accounts-sync-range", "value"),
    prevent_initial_call=True,
)
def sync_account_from_table(
    active_cell: dict[str, object] | None,
    selected_clicks: int | None,
    all_clicks: int | None,
    rows: list[dict[str, object]] | None,
    selected_row_ids: list[str] | None,
    date_preset: str | None,
) -> object:
    account_ids = _manual_sync_account_ids(
        active_cell,
        selected_clicks,
        all_clicks,
        rows,
        selected_row_ids,
    )
    if not account_ids:
        return no_update

    SchedulerService().trigger_sync_range_now(
        triggered_by="manual",
        account_ids=account_ids,
        date_preset=date_preset or "last_90_days",
    )
    return html.Span(
        t("sync.triggered"),
        style={"color": "var(--success)", "fontWeight": "600"},
    )


@callback(
    Output("accounts-sync-selection-msg", "children"),
    Input("accounts-table", "selected_row_ids"),
    prevent_initial_call=True,
)
def save_account_sync_selection(selected_row_ids: list[str] | None) -> object:
    with session_scope() as session:
        AdAccountRepository(session).set_sync_enabled(selected_row_ids or [])

    return html.Span(
        t("accounts.sync_selection.saved"),
        style={"color": "var(--text-muted)"},
    )


def _manual_sync_account_ids(
    active_cell: dict[str, object] | None,
    selected_clicks: int | None,
    all_clicks: int | None,
    rows: list[dict[str, object]] | None,
    selected_row_ids: list[str] | None,
) -> list[str]:
    triggered_id = _triggered_id()
    if triggered_id == "accounts-sync-selected-btn" and selected_clicks:
        return selected_row_ids or []

    if triggered_id == "accounts-sync-all-btn" and all_clicks and rows:
        return [str(row.get("account_id") or row.get("id")) for row in rows if row.get("account_id") or row.get("id")]

    if (triggered_id in {None, "accounts-table"}) and active_cell:
        if active_cell.get("column_id") != "sync_action":
            return []
        row_id = active_cell.get("row_id")
        if row_id:
            return [str(row_id)]

        row_index = active_cell.get("row")
        if isinstance(row_index, int) and rows is not None and row_index < len(rows):
            account_id = rows[row_index].get("account_id") or rows[row_index].get("id")
            return [str(account_id)] if account_id else []

    return []


def _triggered_id() -> str | None:
    try:
        value = ctx.triggered_id
    except Exception:
        return None
    return str(value) if value is not None else None
