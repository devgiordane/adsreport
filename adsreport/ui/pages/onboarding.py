import dash
from dash import dcc, html

from adsreport.i18n import t

dash.register_page(__name__, path="/onboarding", title="Setup — AdsReport")

TOTAL_STEPS = 5


def layout() -> object:
    return html.Div(
        html.Div(
            [
                html.H1(t("onboarding.title"), style={"fontSize": "24px", "fontWeight": "700", "marginBottom": "8px"}),
                html.P(t("onboarding.subtitle"), style={"color": "var(--text-muted)", "marginBottom": "32px"}),

                html.Div(
                    [html.Div(className="wizard__step-dot", id=f"wizard-dot-{i}") for i in range(1, TOTAL_STEPS + 1)],
                    className="wizard__progress",
                ),

                dcc.Store(id="wizard-state", storage_type="session", data={"step": 1}),

                # ── Step 1: Language ──────────────────────────────────────────
                html.Div(id="wizard-step-1", children=[
                    html.H2(t("onboarding.step1.title"), style={"fontWeight": "700", "marginBottom": "8px"}),
                    html.P(t("onboarding.step1.subtitle"), style={"color": "var(--text-muted)", "marginBottom": "20px"}),
                    dcc.Dropdown(
                        id="onboarding-locale",
                        options=[
                            {"label": "Português (Brasil)", "value": "pt-BR"},
                            {"label": "English (US)", "value": "en-US"},
                        ],
                        value="pt-BR",
                        clearable=False,
                    ),
                ]),

                # ── Step 2: Admin account ─────────────────────────────────────
                html.Div(id="wizard-step-2", style={"display": "none"}, children=[
                    html.H2(t("onboarding.step2.title"), style={"fontWeight": "700", "marginBottom": "20px"}),
                    html.Div([
                        html.Div([
                            html.Label(t("onboarding.step2.username"), className="form-label"),
                            dcc.Input(id="onboarding-username", type="text",
                                      placeholder=t("onboarding.step2.username.placeholder"),
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
                    ], style={"display": "flex", "flexDirection": "column", "gap": "16px"}),
                ]),

                # ── Step 3: Facebook credentials ──────────────────────────────
                html.Div(id="wizard-step-3", style={"display": "none"}, children=[
                    html.H2(t("onboarding.step3.title"), style={"fontWeight": "700", "marginBottom": "8px"}),
                    html.P(t("onboarding.step3.subtitle"), style={"color": "var(--text-muted)", "marginBottom": "20px"}),
                    html.Div([
                        html.Div([
                            html.Label(t("onboarding.step3.app_id"), className="form-label"),
                            dcc.Input(id="onboarding-app-id", type="text",
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
                        dcc.Store(id="onboarding-fb-accounts", data=[]),
                    ], style={"display": "flex", "flexDirection": "column", "gap": "16px"}),
                ]),

                # ── Step 4: Default ad account ────────────────────────────────
                html.Div(id="wizard-step-4", style={"display": "none"}, children=[
                    html.H2(t("onboarding.step4.title"), style={"fontWeight": "700", "marginBottom": "8px"}),
                    html.P(t("onboarding.step4.subtitle"), style={"color": "var(--text-muted)", "marginBottom": "20px"}),
                    dcc.RadioItems(id="onboarding-account-select", options=[], value=None),
                ]),

                # Step 5: default date range
                html.Div(id="wizard-step-5", style={"display": "none"}, children=[
                    html.H2(t("onboarding.step5.title"), style={"fontWeight": "700", "marginBottom": "20px"}),
                    html.Div([
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
                    ], style={"display": "flex", "flexDirection": "column", "gap": "16px"}),
                ]),

                # ── Navigation buttons ────────────────────────────────────────
                html.Div(
                    [
                        html.Button(t("common.back"), id="wizard-back", className="btn btn--secondary",
                                    style={"display": "none"}),
                        html.Div(style={"flex": "1"}),
                        html.Button(t("common.next"), id="wizard-next", className="btn btn--primary"),
                    ],
                    style={"display": "flex", "alignItems": "center", "marginTop": "32px"},
                ),
                html.Div(id="wizard-error", style={"color": "var(--danger)", "fontSize": "13px", "marginTop": "8px"}),
                dcc.Location(id="onboarding-redirect", refresh=True),
            ],
            className="wizard",
        ),
        style={"minHeight": "100vh", "background": "var(--bg)", "display": "flex", "justifyContent": "center"},
    )
