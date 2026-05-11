import dash
from dash import dcc, html

from adsreport.i18n import t
from adsreport.ui.layouts.auth_layout import auth_layout

dash.register_page(__name__, path="/login", title="Login — AdsReport")


def layout() -> object:
    return auth_layout(
        html.Div(
            [
                html.Div(
                    html.Img(src="/assets/logo.svg", height=32),
                    style={"marginBottom": "32px"},
                ),
                html.H2(
                    t("auth.login.title"),
                    style={"fontSize": "20px", "fontWeight": "700", "marginBottom": "24px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(t("auth.login.username"), className="form-label"),
                                dcc.Input(
                                    id="login-username",
                                    type="text",
                                    placeholder=t("auth.login.username"),
                                    className="form-input",
                                    style={"width": "100%"},
                                    autoFocus=True,
                                    n_submit=0,
                                ),
                            ],
                            className="form-group",
                        ),
                        html.Div(
                            [
                                html.Label(t("auth.login.password"), className="form-label"),
                                dcc.Input(
                                    id="login-password",
                                    type="password",
                                    placeholder="••••••••",
                                    className="form-input",
                                    style={"width": "100%"},
                                    n_submit=0,
                                ),
                            ],
                            className="form-group",
                        ),
                        html.Div(id="login-error", style={"color": "var(--danger)", "fontSize": "13px"}),
                        html.Button(
                            t("auth.login.submit"),
                            id="login-submit",
                            className="btn btn--primary",
                            style={"width": "100%"},
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                ),
                dcc.Location(id="login-redirect", refresh=True),
            ]
        )
    )
