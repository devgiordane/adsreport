"""Dash + Flask application factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flask_login
from dash import Dash
from flask import Flask, redirect, request

from adsreport.constants import LOGIN_LOCKOUT_MINUTES, MAX_LOGIN_ATTEMPTS
from adsreport.core.logging import setup_logging
from adsreport.db.session import init_db

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue


def create_app() -> Dash:
    setup_logging()
    init_db()

    from adsreport.services.config_loader import reload_config

    config = reload_config()

    app = Dash(
        __name__,
        use_pages=True,
        pages_folder="ui/pages",
        assets_folder="ui/assets",
        suppress_callback_exceptions=True,
        title="AdsReport",
        update_title=None,
    )

    server = app.server
    server.config["SECRET_KEY"] = _derive_flask_secret()
    server.config["SESSION_COOKIE_HTTPONLY"] = True
    server.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Only enforce Secure cookies when running behind HTTPS (proxy sets X-Forwarded-Proto)
    server.config["SESSION_COOKIE_SECURE"] = False

    from werkzeug.middleware.proxy_fix import ProxyFix

    server.wsgi_app = ProxyFix(server.wsgi_app, x_for=1, x_proto=1, x_host=1)
    _register_login_rate_limit(server)
    _register_onboarding_redirect(server)

    login_manager = flask_login.LoginManager()
    login_manager.init_app(server)
    login_manager.login_view = "/login"

    @login_manager.user_loader
    def load_user(user_id: str) -> flask_login.UserMixin | None:
        from adsreport.repositories.user_repo import UserRepository

        with UserRepository() as repo:
            return repo.get_by_id(user_id)

    _register_callbacks(app)
    _setup_scheduler(config)

    from adsreport.ui.layouts.base_layout import build_layout

    app.layout = build_layout()

    return app


def _derive_flask_secret() -> str:
    """Load or create an independent Flask session signing secret."""
    import os

    from adsreport.constants import FLASK_SECRET_FILENAME
    from adsreport.core.crypto import _data_dir

    path = _data_dir() / FLASK_SECRET_FILENAME
    if path.exists():
        secret = path.read_text(encoding="utf-8").strip()
        if secret:
            return secret
    secret = os.urandom(32).hex()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(secret, encoding="utf-8")
    path.chmod(0o600)
    return secret


def _register_login_rate_limit(server: Flask) -> None:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        key_func=get_remote_address,
        app=server,
        default_limits=[],
        storage_uri="memory://",
    )

    @server.before_request
    @limiter.limit(
        f"{MAX_LOGIN_ATTEMPTS} per {LOGIN_LOCKOUT_MINUTES} minutes",
        exempt_when=lambda: not _is_dash_login_callback_request(),
    )
    def limit_login_callback() -> None:
        return None


def _is_dash_login_callback_request() -> bool:
    if request.method != "POST" or request.path != "/_dash-update-component":
        return False

    payload = request.get_json(silent=True) or {}
    output = str(payload.get("output", ""))
    if output.startswith("login-redirect."):
        return True

    inputs = payload.get("inputs") or []
    input_ids = {str(item.get("id")) for item in inputs if isinstance(item, dict)}
    return bool({"login-submit", "login-username", "login-password"} & input_ids)


def _register_onboarding_redirect(server: Flask) -> None:
    """Redirect initial page requests to onboarding while setup is incomplete."""

    import flask_login as _fl

    def _logout() -> ResponseReturnValue:
        _fl.logout_user()
        return redirect("/login")

    server.add_url_rule("/logout", "logout", _logout)

    @server.before_request
    def guard_onboarding() -> ResponseReturnValue | None:
        from adsreport.config import get_config

        if request.method != "GET" or _is_onboarding_exempt_path(request.path):
            return None
        if not get_config().onboarding_completed:
            return redirect("/onboarding")
        return None


def _is_onboarding_exempt_path(path: str) -> bool:
    return (
        path in {"/onboarding", "/login", "/logout", "/about", "/favicon.ico"}
        or path.startswith("/assets/")
        or path.startswith("/_dash-")
    )


def _register_callbacks(app: Dash) -> None:
    import importlib

    for module in (
        "adsreport.ui.callbacks.accounts_callbacks",
        "adsreport.ui.callbacks.auth_callbacks",
        "adsreport.ui.callbacks.dashboard_callbacks",
        "adsreport.ui.callbacks.filter_callbacks",
        "adsreport.ui.callbacks.onboarding_callbacks",
        "adsreport.ui.callbacks.settings_callbacks",
    ):
        importlib.import_module(module)


def _setup_scheduler(config: object) -> None:
    from adsreport.services.scheduler_service import SchedulerService

    SchedulerService().start()
