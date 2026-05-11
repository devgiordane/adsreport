from __future__ import annotations

from dash import html

from adsreport.i18n import t


def empty_state(
    variant: str = "no_data",
    on_cta_id: str | None = None,
    seconds: int | None = None,
) -> html.Div:
    title = t(f"empty.{variant}.title")
    subtitle_kwargs = {}
    if variant == "syncing" and seconds is not None:
        subtitle_kwargs["seconds"] = seconds
    subtitle = t(f"empty.{variant}.subtitle", **subtitle_kwargs)

    children: list[object] = [
        html.Div("📭", style={"fontSize": "40px"}),
        html.H3(title, className="empty-state__title"),
        html.P(subtitle, className="empty-state__subtitle"),
    ]

    if variant in ("no_data", "sync_failed") and on_cta_id:
        cta = t(f"empty.{variant}.cta")
        children.append(
            html.Button(cta, id=on_cta_id, className="btn btn--primary")
        )

    return html.Div(children, className="empty-state")
