"""Settings page tab rendering and save callbacks."""

from __future__ import annotations

from dash import Input, Output, callback, dcc, html

from adsreport.i18n import t
from adsreport.services.settings_service import SettingsService


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
                return _facebook_tab(svc)
            case "sync":
                return _sync_tab(svc)
            case "appearance":
                return _appearance_tab(svc)
            case "language":
                return _language_tab(svc)
            case "about":
                return _about_tab()
            case _:
                return html.Div()


def _general_tab(svc: SettingsService) -> object:
    from adsreport.constants import SettingKey

    return html.Div(
        [
            html.Div([
                html.Label(t("settings.general.timezone"), className="form-label"),
                dcc.Input(id="settings-timezone", value=svc.get(SettingKey.TIMEZONE) or "",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.password.title"), className="form-label",
                           style={"fontSize": "16px", "color": "var(--text-primary)", "marginTop": "24px"}),
            ]),
            html.Div([
                html.Label(t("settings.password.current"), className="form-label"),
                dcc.Input(id="settings-pw-current", type="password", className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.password.new"), className="form-label"),
                dcc.Input(id="settings-pw-new", type="password", className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Button(t("settings.password.save"), id="settings-pw-save", className="btn btn--primary"),
            html.Button(t("settings.general.save"), id="settings-general-save",
                        className="btn btn--primary", style={"marginTop": "16px"}),
            html.Div(id="settings-general-msg"),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "12px", "maxWidth": "480px"},
    )


def _facebook_tab(svc: SettingsService) -> object:
    return html.Div(
        [
            html.P(t("settings.facebook.password_required"),
                   style={"color": "var(--text-muted)", "fontSize": "13px"}),
            html.Div([
                html.Label(t("settings.facebook.current_password"), className="form-label"),
                dcc.Input(id="settings-fb-password", type="password",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.facebook.app_id"), className="form-label"),
                dcc.Input(id="settings-fb-app-id", type="text",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.facebook.app_secret"), className="form-label"),
                dcc.Input(id="settings-fb-app-secret", type="password",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.facebook.access_token"), className="form-label"),
                dcc.Input(id="settings-fb-token", type="password",
                          className="form-input", style={"width": "100%"}),
            ], className="form-group"),
            html.Button(t("settings.facebook.test"), id="settings-fb-test", className="btn btn--secondary"),
            html.Button(t("common.save"), id="settings-fb-save", className="btn btn--primary"),
            html.Div(id="settings-fb-msg"),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "12px", "maxWidth": "480px"},
    )


def _sync_tab(svc: SettingsService) -> object:
    from adsreport.constants import SettingKey

    return html.Div(
        [
            html.Div([
                html.Label(t("settings.sync.interval"), className="form-label"),
                dcc.Input(id="settings-sync-interval", type="number",
                          value=svc.get(SettingKey.SYNC_INTERVAL_MINUTES) or 60, min=5, step=5,
                          className="form-input", style={"width": "120px"}),
            ], className="form-group"),
            html.Div([
                html.Label(t("settings.sync.lookback"), className="form-label"),
                dcc.Input(id="settings-sync-lookback", type="number",
                          value=svc.get(SettingKey.SYNC_LOOKBACK_DAYS) or 30, min=1, max=365, step=1,
                          className="form-input", style={"width": "120px"}),
            ], className="form-group"),
            html.Button(t("settings.sync.run_now"), id="settings-sync-now", className="btn btn--secondary"),
            html.Button(t("common.save"), id="settings-sync-save", className="btn btn--primary"),
            html.Div(id="settings-sync-msg"),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "16px", "maxWidth": "480px"},
    )


def _appearance_tab(svc: SettingsService) -> object:
    from adsreport.constants import SettingKey

    return html.Div(
        [
            html.Div([
                html.Label(t("settings.appearance.theme"), className="form-label"),
                dcc.RadioItems(
                    id="settings-theme",
                    options=[
                        {"label": t("settings.appearance.theme.dark"), "value": "dark"},
                        {"label": t("settings.appearance.theme.light"), "value": "light"},
                    ],
                    value=svc.get(SettingKey.THEME) or "dark",
                    inline=True,
                ),
            ], className="form-group"),
            html.Button(t("common.save"), id="settings-appearance-save", className="btn btn--primary"),
            html.Div(id="settings-appearance-msg"),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "16px", "maxWidth": "480px"},
    )


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
            html.Button(t("common.save"), id="settings-locale-save", className="btn btn--primary"),
            html.Div(id="settings-locale-msg"),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "16px", "maxWidth": "480px"},
    )


def _about_tab() -> object:
    import adsreport

    return html.Div(
        [
            html.P(f"{t('about.version')}: {adsreport.__version__}"),
            html.P(f"{t('about.license')}: MIT"),
            html.P(t("about.tagline"), style={"color": "var(--text-muted)"}),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "8px"},
    )
