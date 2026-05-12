"""Onboarding wizard callbacks.

All step components live permanently in the DOM (rendered by onboarding.py).
Visibility is toggled via style updates — this avoids the Dash error
'nonexistent object used in State' that occurs when components are
dynamically added/removed from the layout.
"""

from __future__ import annotations

from dash import Input, Output, State, callback, html, no_update

from adsreport.i18n import t
from adsreport.services.onboarding_service import OnboardingService

_SHOW: dict = {}
_HIDE: dict = {"display": "none"}


# ── Step visibility ───────────────────────────────────────────────────────────

@callback(
    Output("wizard-step-1", "style"),
    Output("wizard-step-2", "style"),
    Output("wizard-step-3", "style"),
    Output("wizard-step-4", "style"),
    Output("wizard-step-5", "style"),
    Output("wizard-back", "style"),
    Output("wizard-next", "children"),
    Input("wizard-state", "data"),
)
def update_visibility(state: dict) -> tuple:
    step = int(state.get("step", 1))
    styles = [_SHOW if i == step else _HIDE for i in range(1, 6)]
    back_style = _HIDE if step == 1 else _SHOW
    next_label = t("common.finish") if step == 5 else t("common.next")
    return (*styles, back_style, next_label)


# ── Progress dots ─────────────────────────────────────────────────────────────

@callback(
    *[Output(f"wizard-dot-{i}", "className") for i in range(1, 6)],
    Input("wizard-state", "data"),
)
def update_dots(state: dict) -> tuple:
    step = int(state.get("step", 1))
    classes = []
    for i in range(1, 6):
        if i < step:
            classes.append("wizard__step-dot wizard__step-dot--done")
        elif i == step:
            classes.append("wizard__step-dot wizard__step-dot--active")
        else:
            classes.append("wizard__step-dot")
    return tuple(classes)


# ── Test Facebook connection (step 3) ─────────────────────────────────────────

@callback(
    Output("onboarding-connection-result", "children"),
    Output("onboarding-fb-accounts", "data"),
    Output("onboarding-account-select", "options"),
    Output("onboarding-account-select", "value"),
    Input("onboarding-test-btn", "n_clicks"),
    State("onboarding-app-id", "value"),
    State("onboarding-app-secret", "value"),
    State("onboarding-access-token", "value"),
    prevent_initial_call=True,
)
def test_connection(
    n_clicks: int | None,
    app_id: str | None,
    app_secret: str | None,
    access_token: str | None,
) -> tuple:
    if not n_clicks:
        return html.Span(), [], [], None

    result = OnboardingService().test_facebook_connection(
        app_id or "", app_secret or "", access_token or ""
    )

    if result.is_ok():
        accounts = result.unwrap()
        options = [{"label": a.get("name", a.get("id", "")), "value": a.get("id", "")}
                   for a in accounts]
        first = options[0]["value"] if options else None
        msg = html.Span(
            t("onboarding.step3.connection_ok", count=len(accounts)),
            style={"color": "var(--success)"},
        )
        return msg, accounts, options, first

    msg = html.Span(
        t("onboarding.step3.connection_fail", error=result.unwrap_err()),
        style={"color": "var(--danger)"},
    )
    return msg, [], [], None


# ── Navigation ────────────────────────────────────────────────────────────────

@callback(
    Output("wizard-state", "data"),
    Output("wizard-error", "children"),
    Output("onboarding-redirect", "href"),
    Output("onboarding-password", "value"),
    Output("onboarding-password-confirm", "value"),
    Input("wizard-next", "n_clicks"),
    Input("wizard-back", "n_clicks"),
    State("wizard-state", "data"),
    State("onboarding-locale", "value"),
    State("onboarding-username", "value"),
    State("onboarding-password", "value"),
    State("onboarding-password-confirm", "value"),
    State("onboarding-app-id", "value"),
    State("onboarding-app-secret", "value"),
    State("onboarding-access-token", "value"),
    State("onboarding-fb-accounts", "data"),
    State("onboarding-account-select", "value"),
    State("onboarding-range", "value"),
    prevent_initial_call=True,
)
def handle_navigation(
    next_clicks: int | None,
    back_clicks: int | None,
    state: dict,
    locale: str | None,
    username: str | None,
    password: str | None,
    password_confirm: str | None,
    app_id: str | None,
    app_secret: str | None,
    access_token: str | None,
    fb_accounts: list,
    account_id: str | None,
    default_range: str | None,
) -> tuple:
    if next_clicks is None and back_clicks is None:
        return no_update, "", no_update, no_update, no_update  # type: ignore[return-value]

    from dash import ctx

    step = int(state.get("step", 1))
    triggered = ctx.triggered_id

    if triggered == "wizard-back":
        return {"step": max(1, step - 1)}, "", no_update, no_update, no_update  # type: ignore[return-value]

    svc = OnboardingService()

    if step == 1:
        svc.save_locale(locale or "pt-BR")

    elif step == 2:
        result = svc.create_admin(username or "admin", password or "", password_confirm or "")
        if result.is_err():
            return no_update, str(result.unwrap_err()), no_update, no_update, no_update  # type: ignore[return-value]
        return {"step": 3}, "", no_update, "", ""  # clear passwords on advance  # type: ignore[return-value]

    elif step == 3:
        if not fb_accounts:
            return no_update, t("onboarding.step3.connection_fail", error="Teste a conexão primeiro."), no_update, no_update, no_update  # type: ignore[return-value]
        svc.save_facebook_credentials(app_id or "", app_secret or "", access_token or "")

    elif step == 4:
        if account_id:
            svc.save_ad_accounts(
                fb_accounts,
                default_fb_account_id=account_id,
                fallback_timezone="America/Sao_Paulo",
            )

    elif step == 5:
        svc.save_preferences(
            kpis=["impressions", "clicks", "ctr", "cpc", "cpm", "spend", "leads", "conversions", "roas"],
            default_range=default_range or "last_7_days",
            sync_interval=60,
        )
        svc.complete()
        return no_update, "", "/", no_update, no_update  # type: ignore[return-value]

    return {"step": min(5, step + 1)}, "", no_update, no_update, no_update  # type: ignore[return-value]
