import dash
from dash import dcc, html

from adsreport.i18n import t
from adsreport.ui.components.empty_state import empty_state
from adsreport.ui.components.filter_bar import filter_bar
from adsreport.ui.components.navbar import navbar
from adsreport.ui.components.sidebar import sidebar

dash.register_page(__name__, path="/", title="Dashboard — AdsReport")


def layout() -> object:
    return html.Div(
        [
            sidebar(active_path="/"),
            html.Div(
                [
                    navbar(t("dashboard.title")),
                    filter_bar(),
                    html.Div(id="dashboard-kpi-grid", className="kpi-grid"),
                    html.Div(
                        [
                            html.Div(id="dashboard-timeseries", style={"flex": "2"}),
                            html.Div(id="dashboard-breakdown", style={"flex": "1"}),
                        ],
                        style={"display": "flex", "gap": "16px"},
                    ),
                    html.Div(id="dashboard-top-campaigns"),
                    dcc.Interval(id="dashboard-poll", interval=30_000, n_intervals=0),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
