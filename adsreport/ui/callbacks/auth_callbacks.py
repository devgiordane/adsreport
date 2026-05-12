from __future__ import annotations

import flask_login
from dash import Input, Output, State, callback, clientside_callback, no_update

from adsreport.i18n import t
from adsreport.services.auth_service import AuthService

# Logout: bypass React Router with a direct window.location assignment
clientside_callback(
    "function(n) { if (n) { window.location.href = '/logout'; } return ''; }",
    Output("nav-logout-btn", "data-clicked"),
    Input("nav-logout-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("login-redirect", "href"),
    Output("login-error", "children"),
    Input("login-submit", "n_clicks"),
    Input("login-username", "n_submit"),
    Input("login-password", "n_submit"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def handle_login(
    _n_clicks: int | None,
    _user_submit: int | None,
    _pass_submit: int | None,
    username: str | None,
    password: str | None,
) -> tuple[str, str]:
    if not username or not password:
        return no_update, t("auth.login.error.invalid")

    result = AuthService().login(username.strip(), password)
    if result.is_ok():
        flask_login.login_user(result.unwrap(), remember=False)
        return "/", ""
    return no_update, t("auth.login.error.invalid")
