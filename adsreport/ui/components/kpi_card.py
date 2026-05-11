from __future__ import annotations

from dash import html

from adsreport.i18n import t


def kpi_card(
    key: str,
    value: str,
    delta: float | None = None,
    tooltip: str | None = None,
) -> html.Div:
    label = t(f"dashboard.kpi.{key}")
    tip = tooltip or t(f"dashboard.kpi.{key}.tooltip")

    delta_el = None
    if delta is not None:
        direction = "up" if delta >= 0 else "down"
        text = t(f"dashboard.kpi.delta.{direction}", value=f"{abs(delta):.1f}")
        delta_el = html.Span(text, className=f"kpi-card__delta kpi-card__delta--{direction}")

    return html.Div(
        [
            html.Span(label, className="kpi-card__label", title=tip),
            html.Span(value, className="kpi-card__value"),
            delta_el or html.Span(),
        ],
        className="kpi-card",
    )
