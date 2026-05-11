from __future__ import annotations

from dash import html


def auth_layout(children: object) -> html.Div:
    return html.Div(
        html.Div(
            children,
            style={
                "width": "100%",
                "maxWidth": "400px",
                "padding": "40px",
                "background": "var(--surface)",
                "border": "1px solid var(--border)",
                "borderRadius": "var(--radius-lg)",
            },
        ),
        style={
            "minHeight": "100vh",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "background": "var(--bg)",
        },
    )
