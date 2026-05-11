"""Cleanup job: purge old sync_runs and expired cache entries."""

from __future__ import annotations

from datetime import timedelta

from adsreport.core.logging import get_logger
from adsreport.core.time import utcnow

logger = get_logger(__name__)

SYNC_RUN_RETENTION_DAYS = 90


def run_cleanup() -> None:
    _purge_old_sync_runs()
    _clear_memory_cache()
    logger.info("cleanup_complete")


def _purge_old_sync_runs() -> None:
    from sqlalchemy import delete

    from adsreport.db.models.sync_run import SyncRun
    from adsreport.db.session import get_session

    cutoff = utcnow() - timedelta(days=SYNC_RUN_RETENTION_DAYS)
    with get_session() as session:
        result = session.execute(delete(SyncRun).where(SyncRun.started_at < cutoff))
        session.commit()
        deleted = result.rowcount
    if deleted:
        logger.info("cleanup_sync_runs", deleted=deleted)


def _clear_memory_cache() -> None:
    from adsreport.services.cache_service import clear_all

    clear_all()
