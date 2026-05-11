"""Periodic sync job — invoked by APScheduler, also callable directly for testing."""

from __future__ import annotations

from adsreport.core.logging import get_logger

logger = get_logger(__name__)


def run_sync(triggered_by: str = "scheduler") -> None:
    """Sync all active ad accounts for the configured lookback window."""
    from adsreport.config import get_config
    from adsreport.core.time import date_range
    from adsreport.repositories.ad_account_repo import AdAccountRepository
    from adsreport.services.ads_sync_service import AdsSyncService
    from adsreport.services.facebook_client import FacebookClient

    config = get_config()
    if not config.is_facebook_configured():
        logger.warning("sync_skipped", reason="facebook_not_configured")
        return

    fb = FacebookClient(
        config.facebook.app_id,
        config.facebook.app_secret,
        config.facebook.access_token,
        config.facebook.api_version,
    )

    service = AdsSyncService(fb)
    date_from, date_to = date_range(f"last_{config.sync.lookback_days}_days")
    runs = service.sync_all_accounts(date_from, date_to, triggered_by)

    for run in runs:
        logger.info("sync_run_complete", account_id=run.ad_account_id, status=run.status,
                    upserted=run.records_upserted)
