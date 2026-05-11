"""Dash + Flask application factory."""

from __future__ import annotations

import dash
import flask_login
from dash import Dash

from adsreport.core.logging import setup_logging
from adsreport.db.session import init_db


def create_app() -> Dash:
    setup_logging()
    init_db()

    from adsreport.config import reload_config

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

    login_manager = flask_login.LoginManager()
    login_manager.init_app(server)
    login_manager.login_view = "/login"  # type: ignore[assignment]

    @login_manager.user_loader
    def load_user(user_id: str) -> flask_login.UserMixin | None:
        from adsreport.repositories.user_repo import UserRepository

        return UserRepository().get_by_id(user_id)

    _register_onboarding_redirect(app, config)
    _register_callbacks(app)
    _setup_scheduler(config)

    from adsreport.ui.layouts.base_layout import build_layout

    app.layout = build_layout()

    return app


def _derive_flask_secret() -> str:
    """Derive a stable Flask secret key from the salt file (never from env)."""
    import hashlib
    from adsreport.core.crypto import load_or_create_salt

    salt = load_or_create_salt()
    return hashlib.sha256(salt + b"flask-secret").hexdigest()


def _register_onboarding_redirect(app: Dash, config: object) -> None:
    """Middleware: redirect to /onboarding when setup is incomplete."""
    from dash import Input, Output, callback, no_update
    import dash

    @callback(
        Output("_onboarding-redirect", "href"),
        Input("_location", "pathname"),
        prevent_initial_call=False,
    )
    def guard(pathname: str) -> str:
        from adsreport.config import get_config

        cfg = get_config()
        exempt = {"/onboarding", "/login", "/about"}
        if not cfg.onboarding_completed and pathname not in exempt:
            return "/onboarding"
        return no_update  # type: ignore[return-value]


def _register_callbacks(app: Dash) -> None:
    from adsreport.ui.callbacks import (
        auth_callbacks,
        dashboard_callbacks,
        onboarding_callbacks,
        settings_callbacks,
    )


def _setup_scheduler(config: object) -> None:
    from adsreport.services.scheduler_service import SchedulerService

    SchedulerService().start()
