import dash
from dash import dcc, html

import adsreport
from adsreport.i18n import t
from adsreport.ui.components.navbar import navbar
from adsreport.ui.components.sidebar import sidebar

dash.register_page(__name__, path="/about", title="About — AdsReport")


def layout() -> object:
    return html.Div(
        [
            sidebar(active_path="/about"),
            html.Div(
                [
                    navbar(t("about.title")),
                    html.Div(
                        [
                            html.Img(src="/assets/logo.svg", height=40, style={"marginBottom": "16px"}),
                            html.P(t("about.tagline"), style={"color": "var(--text-muted)", "maxWidth": "480px"}),
                            html.Div(style={"height": "24px"}),
                            html.Div(
                                [
                                    html.Span(t("about.version"), style={"color": "var(--text-muted)"}),
                                    html.Span(f" {adsreport.__version__}", style={"fontWeight": "600"}),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Span(t("about.license"), style={"color": "var(--text-muted)"}),
                                    html.Span(" MIT"),
                                ]
                            ),
                            html.Div(style={"height": "24px"}),
                            html.Div(
                                [
                                    dcc.Link(
                                        t("about.github"),
                                        href="https://github.com/adsreport/adsreport",
                                        target="_blank",
                                        className="btn btn--secondary",
                                    ),
                                    dcc.Link(
                                        t("about.report_issue"),
                                        href="https://github.com/adsreport/adsreport/issues/new",
                                        target="_blank",
                                        className="btn btn--secondary",
                                    ),
                                ],
                                style={"display": "flex", "gap": "12px"},
                            ),
                            html.Div(style={"height": "32px"}),
                            html.P(t("about.credits"), style={"color": "var(--text-muted)", "fontSize": "13px"}),
                        ],
                        className="card",
                        style={"maxWidth": "560px"},
                    ),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
