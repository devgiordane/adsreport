from __future__ import annotations

import dash
from dash import dcc, html


def build_layout() -> html.Div:
    return html.Div(
        [
            dcc.Location(id="_location", refresh=False),
            dcc.Store(id="filter-store", storage_type="session"),
            dcc.Interval(id="_sync-poll", interval=30_000, n_intervals=0),
            html.Div(id="app-shell", children=dash.page_container),
        ],
        id="app-root",
    )
