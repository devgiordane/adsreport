"""Onboarding wizard callbacks — step rendering and navigation."""

from __future__ import annotations

from dash import Input, Output, State, callback, dcc, html, no_update

from adsreport.i18n import t
from adsreport.services.onboarding_service import OnboardingService


def _render_step(step: int, data: dict[str, object]) -> object:
    match step:
        case 1:
            return html.Div(
                [
                    html.H2(t("onboarding.step1.title"), style={"fontWeight": "700", "marginBottom": "8px"}),
                    html.P(t("onboarding.step1.subtitle"), style={"color": "var(--text-muted)", "marginBottom": "20px"}),
                    dcc.Dropdown(
                        id="onboarding-locale",
                        options=[
                            {"label": "Português (Brasil)", "value": "pt-BR"},
                            {"label": "English (US)", "value": "en-US"},
                        ],
                        value=data.get("locale", "pt-BR"),
                        clearable=False,
                    ),
                ]
            )
        case 2:
            return html.Div(
                [
                    html.H2(t("onboarding.step2.title"), style={"fontWeight": "700", "marginBottom": "20px"}),
                    html.Div(
                        [
                            html.Div([
                                html.Label(t("onboarding.step2.username"), className="form-label"),
                                dcc.Input(id="onboarding-username", type="text",
                                          placeholder=t("onboarding.step2.username.placeholder"),
                                          value=str(data.get("username", "")),
                                          className="form-input", style={"width": "100%"}),
                            ], className="form-group"),
                            html.Div([
                                html.Label(t("onboarding.step2.password"), className="form-label"),
                                dcc.Input(id="onboarding-password", type="password",
                                          placeholder=t("onboarding.step2.password.placeholder"),
                                          className="form-input", style={"width": "100%"}),
                            ], className="form-group"),
                            html.Div([
                                html.Label(t("onboarding.step2.password_confirm"), className="form-label"),
                                dcc.Input(id="onboarding-password-confirm", type="password",
                                          className="form-input", style={"width": "100%"}),
                            ], className="form-group"),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                    ),
                ]
            )
        case 3:
            return html.Div(
                [
                    html.H2(t("onboarding.step3.title"), style={"fontWeight": "700", "marginBottom": "8px"}),
                    html.P(t("onboarding.step3.subtitle"), style={"color": "var(--text-muted)", "marginBottom": "20px"}),
                    html.Div(
                        [
                            html.Div([
                                html.Label(t("onboarding.step3.app_id"), className="form-label"),
                                dcc.Input(id="onboarding-app-id", type="text",
                                          value=str(data.get("app_id", "")),
                                          className="form-input", style={"width": "100%"}),
                            ], className="form-group"),
                            html.Div([
                                html.Label(t("onboarding.step3.app_secret"), className="form-label"),
                                dcc.Input(id="onboarding-app-secret", type="password",
                                          className="form-input", style={"width": "100%"}),
                            ], className="form-group"),
                            html.Div([
                                html.Label(t("onboarding.step3.access_token"), className="form-label"),
                                dcc.Input(id="onboarding-access-token", type="password",
                                          className="form-input", style={"width": "100%"}),
                            ], className="form-group"),
                            html.Button(t("onboarding.step3.test_connection"),
                                        id="onboarding-test-btn", className="btn btn--secondary"),
                            html.Div(id="onboarding-connection-result"),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                    ),
                ]
            )
        case 4:
            accounts = data.get("fb_accounts") or []
            options = [{"label": a.get("name", a.get("id")), "value": a.get("id")} for a in accounts]
            return html.Div(
                [
                    html.H2(t("onboarding.step4.title"), style={"fontWeight": "700", "marginBottom": "8px"}),
                    html.P(t("onboarding.step4.subtitle"), style={"color": "var(--text-muted)", "marginBottom": "20px"}),
                    dcc.RadioItems(id="onboarding-account-select", options=options, value=options[0]["value"] if options else None),
                ]
            )
        case 5:
            return html.Div(
                [
                    html.H2(t("onboarding.step5.title"), style={"fontWeight": "700", "marginBottom": "20px"}),
                    html.Div([
                        html.Label(t("onboarding.step5.theme"), className="form-label"),
                        dcc.RadioItems(
                            id="onboarding-theme",
                            options=[
                                {"label": t("settings.appearance.theme.dark"), "value": "dark"},
                                {"label": t("settings.appearance.theme.light"), "value": "light"},
                            ],
                            value=str(data.get("theme", "dark")),
                            inline=True,
                        ),
                    ], className="form-group"),
                    html.Div([
                        html.Label(t("onboarding.step5.range"), className="form-label"),
                        dcc.Dropdown(
                            id="onboarding-range",
                            options=[
                                {"label": t("filter.period.last_7d"), "value": "last_7_days"},
                                {"label": t("filter.period.last_14d"), "value": "last_14_days"},
                                {"label": t("filter.period.last_30d"), "value": "last_30_days"},
                            ],
                            value="last_7_days",
                            clearable=False,
                        ),
                    ], className="form-group"),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "16px"},
            )
        case _:
            return html.Div()


@callback(
    Output("wizard-step-content", "children"),
    Output("wizard-back", "style"),
    Input("wizard-state", "data"),
)
def render_step(state: dict[str, object]) -> tuple[object, dict[str, str]]:
    step = int(state.get("step", 1))
    data = dict(state.get("data", {}))
    back_style = {"display": "none"} if step == 1 else {}
    return _render_step(step, data), back_style


@callback(
    Output("wizard-state", "data"),
    Output("wizard-error", "children"),
    Output("onboarding-redirect", "href"),
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
    State("onboarding-account-select", "value"),
    State("onboarding-theme", "value"),
    State("onboarding-range", "value"),
    prevent_initial_call=True,
)
def handle_navigation(
    _next: int | None,
    _back: int | None,
    state: dict[str, object],
    locale: str | None,
    username: str | None,
    password: str | None,
    password_confirm: str | None,
    app_id: str | None,
    app_secret: str | None,
    access_token: str | None,
    account_id: str | None,
    theme: str | None,
    default_range: str | None,
) -> tuple[dict[str, object], str, str]:
    from dash import ctx

    step = int(state.get("step", 1))
    data = dict(state.get("data", {}))
    triggered = ctx.triggered_id

    if triggered == "wizard-back":
        return {**state, "step": max(1, step - 1)}, "", no_update  # type: ignore[return-value]

    svc = OnboardingService()
    error = ""

    if step == 1 and locale:
        data["locale"] = locale
        svc.save_locale(locale)

    elif step == 2:
        result = svc.create_admin(username or "", password or "", password_confirm or "")
        if result.is_err():
            return no_update, str(result.unwrap_err()), no_update  # type: ignore[return-value]
        data["username"] = username
        data["password"] = password

    elif step == 3:
        result = svc.test_facebook_connection(app_id or "", app_secret or "", access_token or "")
        if result.is_err():
            return no_update, t("onboarding.step3.connection_fail", error=result.unwrap_err()), no_update  # type: ignore[return-value]
        accounts = result.unwrap()
        data.update({"app_id": app_id, "fb_accounts": accounts})
        svc.save_facebook_credentials(app_id or "", app_secret or "", access_token or "", password or "")

    elif step == 4 and account_id:
        data["account_id"] = account_id
        svc.save_default_account(account_id, "America/Sao_Paulo")

    elif step == 5:
        svc.save_preferences(
            kpis=["impressions", "clicks", "ctr", "cpc", "cpm", "spend", "leads", "conversions", "roas"],
            default_range=default_range or "last_7_days",
            theme=theme or "dark",
            sync_interval=60,
        )
        svc.complete()
        return no_update, "", "/"  # type: ignore[return-value]

    new_step = min(5, step + 1)
    return {"step": new_step, "data": data}, error, no_update  # type: ignore[return-value]
