from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html


def chart_block(
    title: str,
    figure: go.Figure,
    component_id: str,
    height: int = 300,
) -> html.Div:
    figure.update_layout(height=height, margin={"l": 40, "r": 20, "t": 40, "b": 40})
    return html.Div(
        [
            html.H3(title, style={"fontSize": "14px", "fontWeight": "600", "marginBottom": "12px", "color": "var(--text-muted)"}),
            dcc.Graph(
                id=component_id,
                figure=figure,
                config={"displayModeBar": False, "responsive": True},
                style={"borderRadius": "var(--radius-sm)", "overflow": "hidden"},
            ),
        ],
        className="card",
    )


def empty_figure(theme: str = "dark") -> go.Figure:
    from adsreport.ui.theme import plotly_template

    fig = go.Figure()
    fig.update_layout(**plotly_template(theme)["layout"])
    return fig
