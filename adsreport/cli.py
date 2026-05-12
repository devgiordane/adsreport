"""CLI entrypoint: `adsreport start|migrate|reset|reset-password|version`."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

from adsreport import __version__
from adsreport.core.time import month_range

if TYPE_CHECKING:
    from datetime import date

DEFAULT_DATA_DIR = Path.home() / ".adsreport"
DEFAULT_PORT = 8050


def _resolve_data_dir(data_dir: str | None) -> Path:
    env = os.environ.get("ADSREPORT_DATA_DIR")
    if data_dir:
        return Path(data_dir)
    if env:
        return Path(env)
    return DEFAULT_DATA_DIR


def _month_range(month: str) -> tuple[date, date]:
    try:
        year, month_number = [int(part) for part in month.split("-", maxsplit=1)]
        return month_range(year, month_number)
    except (ValueError, TypeError) as exc:
        raise click.BadParameter("Use o formato YYYY-MM, por exemplo 2026-05.") from exc


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
@click.option("--port", default=DEFAULT_PORT, show_default=True, help="HTTP port to listen on.")
@click.option("--data-dir", default=None, help="Directory for the SQLite database and salt file.")
def dev(port: int, data_dir: str | None) -> None:
    """Start the AdsReport web server in development mode (debug enabled)."""
    resolved = _resolve_data_dir(data_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    os.environ["ADSREPORT_DATA_DIR"] = str(resolved)

    from adsreport.app import create_app

    app = create_app()
    click.echo(f"AdsReport {__version__} (dev mode) — http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)


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


@cli.command("export-leads-report")
@click.option("--account-id", required=True, help="Facebook ad account ID, with or without act_.")
@click.option("--month", required=True, help="Reporting month in YYYY-MM format.")
@click.option("--breakdown", default="region", show_default=True, help="Insights breakdown, e.g. region.")
@click.option("--output", type=click.Path(path_type=Path), required=True, help="CSV output path.")
@click.option("--data-dir", default=None, help="Directory for the SQLite database and salt file.")
def export_leads_report(
    account_id: str,
    month: str,
    breakdown: str,
    output: Path,
    data_dir: str | None,
) -> None:
    """Export a monthly lead report by campaign, ad set, ad, and geographic breakdown."""
    resolved = _resolve_data_dir(data_dir)
    os.environ["ADSREPORT_DATA_DIR"] = str(resolved)

    from adsreport.config import get_config
    from adsreport.services.config_loader import reload_config
    from adsreport.services.facebook_client import FacebookClient
    from adsreport.services.leads_report_service import LeadsReportService

    date_from, date_to = _month_range(month)
    reload_config()
    config = get_config()
    if not config.is_facebook_configured():
        click.echo("Facebook credentials are not configured.", err=True)
        sys.exit(1)

    fb = FacebookClient(
        config.facebook.app_id,
        config.facebook.app_secret,
        config.facebook.access_token,
        config.facebook.api_version,
    )
    service = LeadsReportService(fb)
    rows = service.fetch_monthly(account_id, str(date_from), str(date_to), breakdown=breakdown)
    service.export_csv(rows, output, breakdown_label="Região" if breakdown == "region" else breakdown)
    click.echo(f"Exported {len(rows)} rows to {output}")


@cli.command("version")
def version_cmd() -> None:
    """Print the version and exit."""
    click.echo(f"AdsReport {__version__}")
