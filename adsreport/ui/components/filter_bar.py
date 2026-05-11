from __future__ import annotations

from dash import dcc, html

from adsreport.i18n import t


PERIOD_OPTIONS = [
    {"label": t("filter.period.today"), "value": "today"},
    {"label": t("filter.period.yesterday"), "value": "yesterday"},
    {"label": t("filter.period.last_7d"), "value": "last_7_days"},
    {"label": t("filter.period.last_14d"), "value": "last_14_days"},
    {"label": t("filter.period.last_30d"), "value": "last_30_days"},
    {"label": t("filter.period.mtd"), "value": "mtd"},
]


def filter_bar(
    accounts: list[dict[str, str]] | None = None,
    campaigns: list[dict[str, str]] | None = None,
) -> html.Div:
    return html.Div(
        [
            dcc.Dropdown(
                id="filter-period",
                options=PERIOD_OPTIONS,
                value="last_7_days",
                clearable=False,
                style={"minWidth": "160px"},
            ),
            dcc.Dropdown(
                id="filter-account",
                options=accounts or [],
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
                className="btn btn--secondary",
            ),
            dcc.Store(id="filter-store", storage_type="session"),
        ],
        className="filter-bar",
    )
