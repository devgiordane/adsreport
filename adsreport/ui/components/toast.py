from __future__ import annotations

from dash import html


def toast(message: str, variant: str = "info") -> html.Div:
    return html.Div(message, className=f"toast toast--{variant}", id="toast-message")


def toast_container() -> html.Div:
    return html.Div(id="toast-container", children=[])
