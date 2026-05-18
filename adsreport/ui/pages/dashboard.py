import dash
from dash import dcc, html

from adsreport.i18n import t
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
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button(
                                        t("dashboard.export_pdf"),
                                        id="dashboard-export-pdf-btn",
                                        n_clicks=0,
                                        className="btn btn--secondary dashboard-export-button",
                                    ),
                                    dcc.Download(id="dashboard-pdf-download"),
                                ],
                                className="dashboard-export-actions__controls",
                            ),
                            html.Div(id="dashboard-export-status", className="dashboard-export-status"),
                        ],
                        className="dashboard-export-actions",
                    ),
                    filter_bar(),
                    html.Div(id="dashboard-sync-msg", style={"fontSize": "13px"}),
                    html.Div(
                        [
                            html.Div(id="dashboard-kpi-grid", className="kpi-grid"),
                            html.Div(
                                [
                                    html.Div(id="dashboard-timeseries", className="dashboard-chart-main"),
                                    html.Div(id="dashboard-breakdown", className="dashboard-chart-side"),
                                ],
                                className="dashboard-chart-row",
                            ),
                            html.Div(id="dashboard-top-campaigns"),
                        ],
                        id="dashboard-report",
                        className="dashboard-report-a4",
                    ),
                    dcc.Interval(id="dashboard-poll", interval=30_000, n_intervals=0),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
