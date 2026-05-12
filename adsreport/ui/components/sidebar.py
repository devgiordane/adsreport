from __future__ import annotations

from dash import dcc, html

from adsreport.i18n import t


def sidebar(active_path: str = "/") -> html.Div:
    links = [
        ("/", "nav.dashboard", "📊"),
        ("/campaigns", "nav.campaigns", "📣"),
        ("/accounts", "nav.accounts", "🏢"),
        ("/settings", "nav.settings", "⚙️"),
        ("/about", "nav.about", "ℹ️"),
    ]

    return html.Div(
        [
            html.Div(
                html.Img(src="/assets/logo.svg", height=28),
                className="nav-logo",
            ),
            html.Nav(
                [
                    dcc.Link(
                        [html.Span(icon), t(key_str)],
                        href=href,
                        className=f"nav-link{' nav-link--active' if active_path == href else ''}",
                    )
                    for href, key_str, icon in links
                ]
            ),
            html.Div(style={"flex": "1"}),
            html.Div(
                html.Button(
                    t("nav.logout"),
                    id="nav-logout-btn",
                    n_clicks=0,
                    className="nav-link",
                    style={"background": "none", "border": "none", "cursor": "pointer", "width": "100%", "textAlign": "left"},
                ),
                style={"borderTop": "1px solid var(--border)", "paddingTop": "8px"},
            ),
        ],
        className="sidebar",
    )
