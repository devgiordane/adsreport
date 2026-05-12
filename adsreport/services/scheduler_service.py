"""APScheduler bootstrap and sync trigger."""

from __future__ import annotations

from adsreport.core.logging import get_logger
from adsreport.jobs.cleanup_job import run_cleanup
from adsreport.jobs.sync_job import run_sync, run_sync_range

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
            run_sync,
            "interval",
            minutes=interval,
            id=JOB_SYNC_ID,
            replace_existing=True,
            max_instances=1,
        )
        _scheduler.add_job(
            run_cleanup,
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

    def trigger_sync_now(
        self,
        triggered_by: str = "manual",
        account_ids: list[str] | None = None,
    ) -> None:
        global _scheduler
        if _scheduler is None:
            self.start()
        _scheduler.add_job(  # type: ignore[union-attr]
            run_sync,
            "date",
            kwargs={"triggered_by": triggered_by, "account_ids": account_ids},
            replace_existing=False,
            max_instances=1,
        )
        logger.info("sync_triggered_manually", triggered_by=triggered_by, account_ids=account_ids)

    def trigger_sync_range_now(
        self,
        triggered_by: str = "manual",
        account_ids: list[str] | None = None,
        date_preset: str | None = None,
    ) -> None:
        global _scheduler
        if _scheduler is None:
            self.start()
        _scheduler.add_job(  # type: ignore[union-attr]
            run_sync_range,
            "date",
            kwargs={
                "triggered_by": triggered_by,
                "account_ids": account_ids,
                "date_preset": date_preset,
            },
            replace_existing=False,
            max_instances=1,
        )
        logger.info(
            "sync_range_triggered_manually",
            triggered_by=triggered_by,
            account_ids=account_ids,
            date_preset=date_preset,
        )

    def update_interval(self, minutes: int) -> None:
        global _scheduler
        from adsreport.constants import JOB_SYNC_ID

        if _scheduler is None:
            return
        _scheduler.reschedule_job(JOB_SYNC_ID, trigger="interval", minutes=minutes)
        logger.info("scheduler_interval_updated", minutes=minutes)
