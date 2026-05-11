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
                # Progress dots
                html.Div(
                    [html.Div(className="wizard__step-dot", id=f"wizard-dot-{i}") for i in range(1, TOTAL_STEPS + 1)],
                    className="wizard__progress",
                ),
                dcc.Store(id="wizard-state", storage_type="session", data={"step": 1, "data": {}}),
                html.Div(id="wizard-step-content"),
                html.Div(
                    [
                        html.Button(t("common.back"), id="wizard-back", className="btn btn--secondary", style={"display": "none"}),
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
