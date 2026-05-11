import dash
from dash import html

from adsreport.i18n import t
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
                    html.Div(id="accounts-list"),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
