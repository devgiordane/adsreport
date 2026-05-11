from __future__ import annotations

from dash import html

from adsreport.i18n import t


def navbar(page_title: str = "", sync_status: str | None = None) -> html.Div:
    return html.Div(
        [
            html.H1(page_title, style={"fontSize": "20px", "fontWeight": "600"}),
            html.Div(
                html.Span(sync_status or t("sync.status.never"), style={"color": "var(--text-muted)", "fontSize": "13px"}),
                id="navbar-sync-status",
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "paddingBottom": "16px",
            "borderBottom": "1px solid var(--border)",
        },
    )
