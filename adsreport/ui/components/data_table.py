from __future__ import annotations

from typing import Any

from dash import dash_table, html


def data_table(
    table_id: str,
    columns: list[dict[str, Any]],
    data: list[dict[str, Any]],
    title: str = "",
    page_size: int = 15,
) -> html.Div:
    return html.Div(
        [
            html.H3(
                title,
                style={"fontSize": "14px", "fontWeight": "600", "marginBottom": "12px", "color": "var(--text-muted)"},
            ) if title else None,
            dash_table.DataTable(
                id=table_id,
                columns=columns,
                data=data,
                page_size=page_size,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": "var(--surface-elevated)",
                    "color": "var(--text-muted)",
                    "fontWeight": "600",
                    "fontSize": "12px",
                    "border": "none",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                },
                style_cell={
                    "backgroundColor": "var(--surface)",
                    "color": "var(--text-primary)",
                    "border": "1px solid var(--border)",
                    "fontSize": "13px",
                    "padding": "10px 12px",
                    "fontFamily": "Inter, system-ui, sans-serif",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "var(--surface-elevated)"},
                ],
            ),
        ],
        className="card",
    )
