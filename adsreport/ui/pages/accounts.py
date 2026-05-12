import dash
from dash import dcc, html

from adsreport.i18n import t
from adsreport.ui.components.accounts_list import accounts_list
from adsreport.ui.components.navbar import navbar
from adsreport.ui.components.sidebar import sidebar

dash.register_page(__name__, path="/accounts", title="Accounts — AdsReport")


def layout() -> object:
    return html.Div(
        [
            sidebar(active_path="/accounts"),
            html.Div(
                [
                    navbar(t("accounts.title")),
                    html.Div(
                        [
                            html.Button(
                                t("accounts.refresh_from_facebook"),
                                id="accounts-refresh-btn",
                                n_clicks=0,
                                className="btn btn--secondary",
                            ),
                            dcc.Dropdown(
                                id="accounts-sync-range",
                                options=[
                                    {"label": t("accounts.sync_range.last_30d"), "value": "last_30_days"},
                                    {"label": t("accounts.sync_range.last_90d"), "value": "last_90_days"},
                                    {"label": t("accounts.sync_range.last_365d"), "value": "last_365_days"},
                                ],
                                value="last_90_days",
                                clearable=False,
                                style={"minWidth": "180px"},
                            ),
                            html.Button(
                                t("accounts.sync_selected"),
                                id="accounts-sync-selected-btn",
                                n_clicks=0,
                                className="btn btn--primary",
                            ),
                            html.Button(
                                t("accounts.sync_all"),
                                id="accounts-sync-all-btn",
                                n_clicks=0,
                                className="btn btn--secondary",
                            ),
                            html.Div(id="accounts-refresh-msg", style={"fontSize": "13px"}),
                            html.Div(id="accounts-sync-msg", style={"fontSize": "13px"}),
                            html.Div(id="accounts-sync-selection-msg", style={"fontSize": "13px"}),
                        ],
                        style={"display": "flex", "alignItems": "center", "gap": "12px", "flexWrap": "wrap"},
                    ),
                    html.Div(accounts_list(), id="accounts-list"),
                    dcc.Interval(id="accounts-poll", interval=30_000, n_intervals=0),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
