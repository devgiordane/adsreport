"""Periodic sync job — invoked by APScheduler, also callable directly for testing."""

from __future__ import annotations

from adsreport.config import get_config
from adsreport.core.logging import get_logger
from adsreport.core.time import date_range
from adsreport.db.session import session_scope
from adsreport.services.ads_sync_service import AdsSyncService
from adsreport.services.facebook_client import FacebookClient

logger = get_logger(__name__)


def run_sync(triggered_by: str = "scheduler", account_ids: list[str] | None = None) -> None:
    """Sync selected ad accounts, or all sync-enabled accounts, for the configured lookback."""
    run_sync_range(triggered_by=triggered_by, account_ids=account_ids)


def run_sync_range(
    triggered_by: str = "scheduler",
    account_ids: list[str] | None = None,
    date_preset: str | None = None,
) -> None:
    """Sync selected accounts for either a preset window or the configured lookback."""
    config = get_config()
    if config.facebook.credentials_locked:
        logger.warning("sync_skipped", reason="facebook_credentials_locked")
        return
    if not config.is_facebook_configured():
        logger.warning("sync_skipped", reason="facebook_not_configured")
        return

    fb = FacebookClient(
        config.facebook.app_id,
        config.facebook.app_secret,
        config.facebook.access_token,
        config.facebook.api_version,
    )

    preset = date_preset or f"last_{config.sync.lookback_days}_days"
    date_from, date_to = date_range(preset)
    with session_scope() as session:
        service = AdsSyncService(fb, session=session)
        if account_ids:
            runs = [
                service.sync_account(account_id, date_from, date_to, triggered_by)
                for account_id in account_ids
            ]
        else:
            runs = service.sync_all_accounts(date_from, date_to, triggered_by)

        for run in runs:
            logger.info("sync_run_complete", account_id=run.ad_account_id, status=run.status,
                        upserted=run.records_upserted)
