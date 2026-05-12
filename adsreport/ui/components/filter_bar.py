from __future__ import annotations

from dash import dcc, html

from adsreport.db.session import session_scope
from adsreport.i18n import t
from adsreport.repositories.ad_account_repo import AdAccountRepository


def period_options() -> list[dict[str, str]]:
    return [
        {"label": t("filter.period.today"), "value": "today"},
        {"label": t("filter.period.yesterday"), "value": "yesterday"},
        {"label": t("filter.period.last_7d"), "value": "last_7_days"},
        {"label": t("filter.period.last_14d"), "value": "last_14_days"},
        {"label": t("filter.period.last_30d"), "value": "last_30_days"},
        {"label": t("filter.period.last_month"), "value": "last_month"},
        {"label": t("filter.period.mtd"), "value": "mtd"},
    ]


def filter_bar(
    accounts: list[dict[str, str]] | None = None,
    campaigns: list[dict[str, str]] | None = None,
) -> html.Div:
    account_options = accounts if accounts is not None else _account_options()

    return html.Div(
        [
            dcc.Dropdown(
                id="filter-period",
                options=period_options(),
                value="last_7_days",
                clearable=False,
                style={"minWidth": "160px"},
            ),
            dcc.Dropdown(
                id="filter-account",
                options=account_options,
                placeholder=t("filter.account"),
                multi=True,
                style={"minWidth": "200px"},
            ),
            dcc.Dropdown(
                id="filter-campaign",
                options=campaigns or [],
                placeholder=t("filter.campaign"),
                multi=True,
                style={"minWidth": "200px"},
            ),
            html.Button(
                t("filter.refresh"),
                id="filter-refresh-btn",
                n_clicks=0,
                className="btn btn--secondary",
            ),
            dcc.Interval(id="filter-account-options-poll", interval=30_000, n_intervals=0),
            dcc.Store(id="filter-store", storage_type="session"),
        ],
        className="filter-bar",
    )


def _account_options() -> list[dict[str, str]]:
    with session_scope() as session:
        accounts = AdAccountRepository(session).get_all_active()
        return [
            {
                "label": f"{account.name} ({account.fb_account_id})",
                "value": account.id,
            }
            for account in accounts
        ]
