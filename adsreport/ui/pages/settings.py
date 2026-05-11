import dash
from dash import dcc, html

from adsreport.i18n import t
from adsreport.ui.components.navbar import navbar
from adsreport.ui.components.sidebar import sidebar

dash.register_page(__name__, path="/settings", title="Settings — AdsReport")

TABS = [
    ("general", "settings.tab.general"),
    ("facebook", "settings.tab.facebook"),
    ("sync", "settings.tab.sync"),
    ("appearance", "settings.tab.appearance"),
    ("language", "settings.tab.language"),
    ("about", "settings.tab.about"),
]


def layout() -> object:
    return html.Div(
        [
            sidebar(active_path="/settings"),
            html.Div(
                [
                    navbar(t("settings.title")),
                    dcc.Tabs(
                        id="settings-tabs",
                        value="general",
                        children=[
                            dcc.Tab(label=t(label_key), value=tab_id)
                            for tab_id, label_key in TABS
                        ],
                    ),
                    html.Div(id="settings-tab-content", style={"marginTop": "24px"}),
                    html.Div(id="settings-toast"),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
