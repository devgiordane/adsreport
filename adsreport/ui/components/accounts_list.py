from __future__ import annotations

from typing import TYPE_CHECKING

from dash import dash_table, html

from adsreport.db.session import session_scope
from adsreport.i18n import t
from adsreport.repositories.ad_account_repo import AdAccountRepository

if TYPE_CHECKING:
    from datetime import datetime

    from adsreport.db.models.ad_account import AdAccount


def accounts_list() -> object:
    with session_scope() as session:
        accounts = AdAccountRepository(session).get_all()
        rows = [_account_row(account) for account in accounts]

    if not rows:
        return _empty_accounts()

    columns = [
        {"name": t("accounts.table.name"), "id": "name"},
        {"name": t("accounts.table.fb_account"), "id": "fb_account_id"},
        {"name": t("accounts.table.status"), "id": "status"},
        {"name": t("accounts.currency"), "id": "currency"},
        {"name": t("accounts.timezone"), "id": "timezone"},
        {"name": t("accounts.last_synced"), "id": "last_synced_at"},
        {"name": t("accounts.actions"), "id": "sync_action"},
    ]
    return html.Div(
        [
            html.H3(
                t("accounts.title"),
                style={
                    "fontSize": "14px",
                    "fontWeight": "600",
                    "marginBottom": "12px",
                    "color": "var(--text-muted)",
                },
            ),
            dash_table.DataTable(
                id="accounts-table",
                columns=columns,
                data=rows,
                page_size=20,
                sort_action="native",
                filter_action="native",
                row_selectable="multi",
                selected_row_ids=[
                    row["id"]
                    for row in rows
                    if row["sync_enabled"] == "true"
                ],
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": "var(--surface-elevated)",
                    "color": "var(--text-muted)",
                    "fontWeight": "600",
                    "fontSize": "12px",
                    "border": "none",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                },
                style_cell={
                    "backgroundColor": "var(--surface)",
                    "color": "var(--text-primary)",
                    "border": "1px solid var(--border)",
                    "fontSize": "13px",
                    "padding": "10px 12px",
                    "fontFamily": "Inter, system-ui, sans-serif",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "var(--surface-elevated)"},
                    {
                        "if": {"column_id": "sync_action"},
                        "color": "var(--accent)",
                        "fontWeight": "600",
                        "cursor": "pointer",
                    },
                ],
            ),
        ],
        className="card",
    )


def _account_row(account: AdAccount) -> dict[str, str]:
    name = account.name
    if account.is_default:
        name = f"{name} ({t('accounts.default')})"

    return {
        "name": name,
        "id": account.id,
        "account_id": account.id,
        "fb_account_id": account.fb_account_id,
        "status": _status_label(account.status),
        "currency": account.currency,
        "timezone": account.timezone,
        "last_synced_at": _format_last_synced(account.last_synced_at),
        "sync_action": t("accounts.sync_now"),
        "sync_enabled": "true" if account.sync_enabled else "false",
    }


def _status_label(status: str) -> str:
    if status in {"active", "disabled"}:
        return t(f"accounts.status.{status}")
    return status.replace("_", " ").title()


def _format_last_synced(value: datetime | None) -> str:
    if value is None:
        return t("accounts.never_synced")
    return value.strftime("%Y-%m-%d %H:%M")


def _empty_accounts() -> html.Div:
    return html.Div(
        [
            html.Div("AD", style={"fontSize": "32px", "fontWeight": "700"}),
            html.H3(t("accounts.empty.title"), className="empty-state__title"),
            html.P(t("accounts.empty.subtitle"), className="empty-state__subtitle"),
        ],
        className="empty-state",
    )
