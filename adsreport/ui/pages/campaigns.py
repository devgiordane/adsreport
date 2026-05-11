import dash
from dash import html

from adsreport.i18n import t
from adsreport.ui.components.filter_bar import filter_bar
from adsreport.ui.components.navbar import navbar
from adsreport.ui.components.sidebar import sidebar

dash.register_page(__name__, path="/campaigns", title="Campaigns — AdsReport")


def layout() -> object:
    return html.Div(
        [
            sidebar(active_path="/campaigns"),
            html.Div(
                [
                    navbar(t("campaigns.title")),
                    filter_bar(),
                    html.Div(id="campaigns-table-container"),
                    html.Div(id="campaigns-drill-chart"),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
