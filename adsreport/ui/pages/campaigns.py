import dash
from dash import dash_table, dcc, html

from adsreport.i18n import t
from adsreport.ui.components.filter_bar import filter_bar
from adsreport.ui.components.navbar import navbar
from adsreport.ui.components.sidebar import sidebar

dash.register_page(__name__, path="/campaigns", title="Campaigns — AdsReport")

_HEADER_STYLE = {
    "backgroundColor": "var(--surface-elevated)",
    "color": "var(--text-muted)",
    "fontWeight": "600",
    "fontSize": "12px",
    "border": "none",
    "textTransform": "uppercase",
    "letterSpacing": "0.05em",
}
_CELL_STYLE = {
    "backgroundColor": "var(--surface)",
    "color": "var(--text-primary)",
    "border": "1px solid var(--border)",
    "fontSize": "13px",
    "padding": "10px 12px",
    "fontFamily": "Inter, system-ui, sans-serif",
}


def layout() -> object:
    return html.Div(
        [
            sidebar(active_path="/campaigns"),
            html.Div(
                [
                    navbar(t("campaigns.title")),
                    filter_bar(),
                    html.Div(id="campaigns-table-msg"),
                    html.Div(
                        [
                            dash_table.DataTable(
                                id="campaigns-table",
                                columns=[],
                                data=[],
                                page_size=20,
                                sort_action="native",
                                filter_action="native",
                                hidden_columns=["entity_id"],
                                style_table={"overflowX": "auto"},
                                style_header=_HEADER_STYLE,
                                style_cell=_CELL_STYLE,
                                style_data_conditional=[
                                    {"if": {"row_index": "odd"}, "backgroundColor": "var(--surface-elevated)"},
                                ],
                            ),
                        ],
                        id="campaigns-table-container",
                        className="card",
                        style={"display": "none"},
                    ),
                    html.Div(id="campaigns-drill-chart"),
                    dcc.Interval(id="campaigns-poll", interval=30_000, n_intervals=0),
                ],
                className="main-content",
            ),
        ],
        className="app-shell",
    )
