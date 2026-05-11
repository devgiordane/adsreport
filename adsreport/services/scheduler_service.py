"""APScheduler bootstrap and sync trigger."""

from __future__ import annotations

from adsreport.core.logging import get_logger

logger = get_logger(__name__)

_scheduler = None


class SchedulerService:
    def start(self) -> None:
        global _scheduler
        if _scheduler is not None and _scheduler.running:
            return

        from apscheduler.schedulers.background import BackgroundScheduler

        from adsreport.config import get_config
        from adsreport.constants import JOB_CLEANUP_ID, JOB_SYNC_ID

        config = get_config()
        interval = config.sync.interval_minutes

        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.add_job(
            _run_sync,
            "interval",
            minutes=interval,
            id=JOB_SYNC_ID,
            replace_existing=True,
            max_instances=1,
        )
        _scheduler.add_job(
            _run_cleanup,
            "cron",
            hour=3,
            minute=0,
            id=JOB_CLEANUP_ID,
            replace_existing=True,
        )
        _scheduler.start()
        logger.info("scheduler_started", sync_interval_minutes=interval)

    def stop(self) -> None:
        global _scheduler
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=False)
            _scheduler = None

    def trigger_sync_now(self, triggered_by: str = "manual") -> None:
        from apscheduler.schedulers.background import BackgroundScheduler

        global _scheduler
        if _scheduler is None:
            self.start()
        _scheduler.add_job(  # type: ignore[union-attr]
            _run_sync,
            "date",
            kwargs={"triggered_by": triggered_by},
            replace_existing=False,
            max_instances=1,
        )
        logger.info("sync_triggered_manually", triggered_by=triggered_by)

    def update_interval(self, minutes: int) -> None:
        global _scheduler
        from adsreport.constants import JOB_SYNC_ID

        if _scheduler is None:
            return
        _scheduler.reschedule_job(JOB_SYNC_ID, trigger="interval", minutes=minutes)
        logger.info("scheduler_interval_updated", minutes=minutes)


def _run_sync(triggered_by: str = "scheduler") -> None:
    try:
        from adsreport.config import get_config
        from adsreport.constants import SyncTrigger
        from adsreport.core.time import date_range
        from adsreport.repositories.ad_account_repo import AdAccountRepository
        from adsreport.services.ads_sync_service import AdsSyncService
        from adsreport.services.facebook_client import FacebookClient

        config = get_config()
        if not config.is_facebook_configured():
            return

        fb = FacebookClient(
            config.facebook.app_id,
            config.facebook.app_secret,
            config.facebook.access_token,
            config.facebook.api_version,
        )
        service = AdsSyncService(fb)
        date_from, date_to = date_range(f"last_{config.sync.lookback_days}_days")
        service.sync_all_accounts(date_from, date_to, triggered_by)
    except Exception as exc:
        logger.error("sync_job_error", error=str(exc))


def _run_cleanup() -> None:
    try:
        from adsreport.jobs.cleanup_job import run_cleanup

        run_cleanup()
    except Exception as exc:
        logger.error("cleanup_job_error", error=str(exc))
