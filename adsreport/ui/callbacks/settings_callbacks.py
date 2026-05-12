"""Settings page — tab rendering + action callbacks.

Each tab's action buttons share one callback (distinguished by ctx.triggered_id)
to avoid the allow_duplicate=True issues in Dash 2.x.
"""

from __future__ import annotations

from dash import Input, Output, State, callback, ctx, dcc, html, no_update

from adsreport.i18n import t
from adsreport.services.settings_service import SettingsService

# ── Tab rendering ─────────────────────────────────────────────────────────────

@callback(
    Output("settings-tab-content", "children"),
    Input("settings-tabs", "value"),
)
def render_tab(tab: str) -> object:
    with SettingsService() as svc:
        match tab:
            case "general":
                return _general_tab(svc)
            case "facebook":
                return _facebook_tab()
            case "sync":
                return _sync_tab(svc)
            case "language":
                return _language_tab(svc)
            case "about":
                return _about_tab()
            case _:
                return html.Div()


# ── Facebook ──────────────────────────────────────────────────────────────────

def _facebook_tab() -> object:
    return html.Div(
        [
            html.Div([
                html.Label(t("settings.facebook.app_id"), className="form-label"),
                dcc.Input(id="settings-fb-app-id", type="text",
                          placeholder="123456789012345",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.facebook.app_secret"), className="form-label"),
                dcc.Input(id="settings-fb-app-secret", type="password",
                          placeholder="••••••••••••••••",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.facebook.access_token"), className="form-label"),
                dcc.Input(id="settings-fb-token", type="password",
                          placeholder="EAAB...",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div(
                [
                    html.Button(t("settings.facebook.test"), id="settings-fb-test",
                                n_clicks=0, className="btn btn--secondary"),
                    html.Button(t("common.save"), id="settings-fb-save",
                                n_clicks=0, className="btn btn--primary"),
                ],
                style={"display": "flex", "gap": "8px"},
            ),
            html.Div(id="settings-fb-msg", style={"fontSize": "13px", "marginTop": "4px"}),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "12px", "maxWidth": "480px"},
    )


@callback(
    Output("settings-fb-msg", "children"),
    Input("settings-fb-test", "n_clicks"),
    Input("settings-fb-save", "n_clicks"),
    State("settings-fb-app-id", "value"),
    State("settings-fb-app-secret", "value"),
    State("settings-fb-token", "value"),
    prevent_initial_call=True,
)
def facebook_actions(
    test_clicks: int,
    save_clicks: int,
    app_id: str | None,
    app_secret: str | None,
    token: str | None,
) -> object:
    if not test_clicks and not save_clicks:
        return no_update
    triggered = ctx.triggered_id

    if triggered == "settings-fb-test":
        if not app_id or not app_secret or not token:
            return html.Span("Preencha App ID, App Secret e Access Token primeiro.",
                             style={"color": "var(--danger)"})
        from adsreport.services.onboarding_service import OnboardingService

        result = OnboardingService().test_facebook_connection(app_id, app_secret, token)
        if result.is_ok():
            accounts = result.unwrap()
            return html.Span(
                t("onboarding.step3.connection_ok", count=len(accounts)),
                style={"color": "var(--success)", "fontWeight": "600"},
            )
        return html.Span(
            t("onboarding.step3.connection_fail", error=result.unwrap_err()),
            style={"color": "var(--danger)"},
        )

    if triggered == "settings-fb-save":
        if not app_id or not app_secret or not token:
            return html.Span("Preencha App ID, App Secret e Access Token.",
                             style={"color": "var(--danger)"})
        try:
            from adsreport.services.onboarding_service import OnboardingService

            svc = OnboardingService()
            svc.save_facebook_credentials(app_id, app_secret, token)
            result = svc.test_facebook_connection(app_id, app_secret, token)
            if result.is_ok():
                accounts = result.unwrap()
                svc.save_ad_accounts(accounts)
                message = (
                    f"{t('settings.general.saved')} "
                    f"{t('onboarding.step3.connection_ok', count=len(accounts))}"
                )
                return html.Span(message, style={"color": "var(--success)", "fontWeight": "600"})
            return html.Span(
                t("onboarding.step3.connection_fail", error=result.unwrap_err()),
                style={"color": "var(--danger)"},
            )
        except Exception as exc:
            return html.Span(str(exc), style={"color": "var(--danger)"})

    return no_update


# ── General / Password ────────────────────────────────────────────────────────

def _general_tab(svc: SettingsService) -> object:
    from adsreport.constants import SettingKey

    return html.Div(
        [
            html.Div([
                html.Label(t("settings.general.timezone"), className="form-label"),
                dcc.Input(id="settings-timezone", value=svc.get(SettingKey.TIMEZONE) or "",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Button(t("settings.general.save"), id="settings-general-save",
                        n_clicks=0, className="btn btn--primary"),
            html.Hr(style={"border": "none", "borderTop": "1px solid var(--border)", "margin": "8px 0"}),
            html.H3(t("settings.password.title"),
                    style={"fontSize": "15px", "fontWeight": "600", "color": "var(--text-primary)"}),
            html.Div([
                html.Label(t("settings.password.current"), className="form-label"),
                dcc.Input(id="settings-pw-current", type="password",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.password.new"), className="form-label"),
                dcc.Input(id="settings-pw-new", type="password",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.password.confirm"), className="form-label"),
                dcc.Input(id="settings-pw-confirm", type="password",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Button(t("settings.password.save"), id="settings-pw-save",
                        n_clicks=0, className="btn btn--primary"),
            html.Div(id="settings-general-msg", style={"fontSize": "13px"}),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "12px", "maxWidth": "480px"},
    )


@callback(
    Output("settings-general-msg", "children"),
    Input("settings-general-save", "n_clicks"),
    Input("settings-pw-save", "n_clicks"),
    State("settings-timezone", "value"),
    State("settings-pw-current", "value"),
    State("settings-pw-new", "value"),
    State("settings-pw-confirm", "value"),
    prevent_initial_call=True,
)
def general_actions(
    save_clicks: int,
    pw_save_clicks: int,
    timezone: str | None,
    pw_current: str | None,
    pw_new: str | None,
    pw_confirm: str | None,
) -> object:
    if not save_clicks and not pw_save_clicks:
        return no_update
    triggered = ctx.triggered_id

    if triggered == "settings-general-save":
        with SettingsService() as svc:
            from adsreport.constants import SettingKey

            svc.set(SettingKey.TIMEZONE, timezone or "America/Sao_Paulo")
        return html.Span(t("settings.general.saved"),
                         style={"color": "var(--success)", "fontWeight": "600"})

    if triggered == "settings-pw-save":
        if not pw_current or not pw_new:
            return html.Span(t("common.errors.generic"), style={"color": "var(--danger)"})
        if pw_new != pw_confirm:
            return html.Span(t("onboarding.step2.error.password_mismatch"),
                             style={"color": "var(--danger)"})
        import flask_login

        from adsreport.services.auth_service import AuthService

        user = flask_login.current_user
        if not user or not user.is_authenticated:
            return html.Span(t("common.errors.unauthorized"), style={"color": "var(--danger)"})
        result = AuthService().change_password(user, pw_current, pw_new)
        if result.is_ok():
            return html.Span(t("settings.password.success"),
                             style={"color": "var(--success)", "fontWeight": "600"})
        return html.Span(str(result.unwrap_err()), style={"color": "var(--danger)"})

    return no_update


# ── Sync ──────────────────────────────────────────────────────────────────────

def _sync_tab(svc: SettingsService) -> object:
    from adsreport.constants import SettingKey

    last_run = svc.get(SettingKey.SYNC_LAST_RUN_AT) or t("settings.sync.never")
    return html.Div(
        [
            html.Div([
                html.Label(t("settings.sync.interval"), className="form-label"),
                dcc.Input(id="settings-sync-interval", type="number",
                          value=svc.get(SettingKey.SYNC_INTERVAL_MINUTES) or 60,
                          min=5, step=5, className="form-input", style={"width": "120px"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.sync.lookback"), className="form-label"),
                dcc.Input(id="settings-sync-lookback", type="number",
                          value=svc.get(SettingKey.SYNC_LOOKBACK_DAYS) or 30,
                          min=1, max=365, step=1, className="form-input", style={"width": "120px"}),
            ], className="form-group"),
            html.P(f"{t('settings.sync.last_run')}: {last_run}",
                   style={"color": "var(--text-muted)", "fontSize": "13px"}),
            html.Div(
                [
                    html.Button(t("settings.sync.run_now"), id="settings-sync-now",
                                n_clicks=0, className="btn btn--secondary"),
                    html.Button(t("common.save"), id="settings-sync-save",
                                n_clicks=0, className="btn btn--primary"),
                ],
                style={"display": "flex", "gap": "8px"},
            ),
            html.Div(id="settings-sync-msg", style={"fontSize": "13px"}),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "16px", "maxWidth": "480px"},
    )


@callback(
    Output("settings-sync-msg", "children"),
    Input("settings-sync-save", "n_clicks"),
    Input("settings-sync-now", "n_clicks"),
    State("settings-sync-interval", "value"),
    State("settings-sync-lookback", "value"),
    prevent_initial_call=True,
)
def sync_actions(
    save_clicks: int,
    now_clicks: int,
    interval: int | None,
    lookback: int | None,
) -> object:
    if not save_clicks and not now_clicks:
        return no_update
    triggered = ctx.triggered_id

    if triggered == "settings-sync-save":
        with SettingsService() as svc:
            from adsreport.constants import SettingKey

            svc.set(SettingKey.SYNC_INTERVAL_MINUTES, int(interval or 60))
            svc.set(SettingKey.SYNC_LOOKBACK_DAYS, int(lookback or 30))
        from adsreport.services.scheduler_service import SchedulerService

        SchedulerService().update_interval(int(interval or 60))
        return html.Span(t("settings.general.saved"),
                         style={"color": "var(--success)", "fontWeight": "600"})

    if triggered == "settings-sync-now":
        from adsreport.services.scheduler_service import SchedulerService

        SchedulerService().trigger_sync_now(triggered_by="manual")
        return html.Span(t("sync.triggered"),
                         style={"color": "var(--success)", "fontWeight": "600"})

    return no_update


# ── Language ──────────────────────────────────────────────────────────────────

def _language_tab(svc: SettingsService) -> object:
    from adsreport.constants import SettingKey

    return html.Div(
        [
            html.Div([
                html.Label(t("settings.language.label"), className="form-label"),
                dcc.Dropdown(
                    id="settings-locale",
                    options=[
                        {"label": "Português (Brasil)", "value": "pt-BR"},
                        {"label": "English (US)", "value": "en-US"},
                    ],
                    value=svc.get(SettingKey.LOCALE) or "pt-BR",
                    clearable=False,
                    style={"width": "240px"},
                ),
            ], className="form-group"),
            html.Button(t("common.save"), id="settings-locale-save",
                        n_clicks=0, className="btn btn--primary"),
            html.Div(id="settings-locale-msg", style={"fontSize": "13px"}),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "16px", "maxWidth": "480px"},
    )


@callback(
    Output("settings-locale-msg", "children"),
    Input("settings-locale-save", "n_clicks"),
    State("settings-locale", "value"),
    prevent_initial_call=True,
)
def save_locale(n_clicks: int, locale: str | None) -> object:
    if not n_clicks:
        return no_update
    from adsreport.services.i18n_service import I18nService

    I18nService().set_locale(locale or "pt-BR")
    return html.Span(t("settings.general.saved"),
                     style={"color": "var(--success)", "fontWeight": "600"})


# ── About ─────────────────────────────────────────────────────────────────────

def _about_tab() -> object:
    import adsreport

    return html.Div(
        [
            html.Img(src="/assets/logo.svg", height=36, style={"marginBottom": "8px"}),
            html.P(t("about.tagline"), style={"color": "var(--text-muted)", "maxWidth": "400px"}),
            html.Div(style={"height": "8px"}),
            html.P(f"{t('about.version')}: {adsreport.__version__}"),
            html.P(f"{t('about.license')}: MIT"),
            html.Div(style={"height": "8px"}),
            html.Div([
                html.A(t("about.github"),
                       href="https://github.com/adsreport/adsreport",
                       target="_blank", className="btn btn--secondary"),
                html.A(t("about.report_issue"),
                       href="https://github.com/adsreport/adsreport/issues/new",
                       target="_blank", className="btn btn--secondary"),
            ], style={"display": "flex", "gap": "8px"}),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "8px"},
    )
