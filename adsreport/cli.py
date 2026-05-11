"""CLI entrypoint: `adsreport start|migrate|reset|reset-password|version`."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from adsreport import __version__

DEFAULT_DATA_DIR = Path.home() / ".adsreport"
DEFAULT_PORT = 8050


def _resolve_data_dir(data_dir: str | None) -> Path:
    env = os.environ.get("ADSREPORT_DATA_DIR")
    if data_dir:
        return Path(data_dir)
    if env:
        return Path(env)
    return DEFAULT_DATA_DIR


@click.group()
@click.version_option(__version__, prog_name="adsreport")
def cli() -> None:
    """AdsReport — self-hosted Facebook Ads dashboard."""


@cli.command()
@click.option("--port", default=DEFAULT_PORT, show_default=True, help="HTTP port to listen on.")
@click.option("--data-dir", default=None, help="Directory for the SQLite database and salt file.")
@click.option("--debug", is_flag=True, default=False, help="Enable Dash debug mode.")
def start(port: int, data_dir: str | None, debug: bool) -> None:
    """Start the AdsReport web server."""
    resolved = _resolve_data_dir(data_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    os.environ["ADSREPORT_DATA_DIR"] = str(resolved)

    from adsreport.app import create_app

    app = create_app()
    click.echo(f"AdsReport {__version__} — http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)


@cli.command()
@click.option("--data-dir", default=None, help="Directory for the SQLite database.")
def migrate(data_dir: str | None) -> None:
    """Run Alembic migrations to the latest revision."""
    resolved = _resolve_data_dir(data_dir)
    os.environ["ADSREPORT_DATA_DIR"] = str(resolved)

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(Path(__file__).parent / "db" / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    click.echo("Migrations applied.")


@cli.command("reset")
@click.option("--data-dir", default=None)
@click.option("--confirm", is_flag=True, required=True, help="Required to confirm destructive wipe.")
def reset(data_dir: str | None, confirm: bool) -> None:
    """Wipe and recreate the database. Irreversible."""
    resolved = _resolve_data_dir(data_dir)
    db_path = resolved / "data.db"
    salt_path = resolved / ".salt"

    if db_path.exists():
        db_path.unlink()
        click.echo(f"Deleted {db_path}")
    if salt_path.exists():
        salt_path.unlink()
        click.echo(f"Deleted {salt_path}")

    os.environ["ADSREPORT_DATA_DIR"] = str(resolved)
    from adsreport.db.session import init_db

    init_db()
    click.echo("Database reset. Run `adsreport start` to go through onboarding again.")


@cli.command("reset-password")
@click.option("--data-dir", default=None)
def reset_password(data_dir: str | None) -> None:
    """Interactively reset the admin password."""
    resolved = _resolve_data_dir(data_dir)
    os.environ["ADSREPORT_DATA_DIR"] = str(resolved)

    new_pw = click.prompt("New password", hide_input=True, confirmation_prompt=True)
    if len(new_pw) < 8:
        click.echo("Password must be at least 8 characters.", err=True)
        sys.exit(1)

    from adsreport.services.auth_service import AuthService

    AuthService().reset_admin_password(new_pw)
    click.echo("Password updated. All encrypted secrets have been re-encrypted.")


@cli.command("version")
def version_cmd() -> None:
    """Print the version and exit."""
    click.echo(f"AdsReport {__version__}")
