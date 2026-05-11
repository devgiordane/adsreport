"""Incremental sync orchestrator for Facebook Ads data."""

from __future__ import annotations

from datetime import date, datetime, timezone

from adsreport.constants import InsightLevel, SyncStatus, SyncTrigger
from adsreport.core.errors import FacebookError, SyncError
from adsreport.core.logging import get_logger
from adsreport.core.time import utcnow
from adsreport.db.models.insight import Insight
from adsreport.db.models.sync_run import SyncRun
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.repositories.campaign_repo import CampaignRepository
from adsreport.repositories.insight_repo import InsightRepository
from adsreport.repositories.sync_run_repo import SyncRunRepository
from adsreport.services.facebook_client import FacebookClient

logger = get_logger(__name__)


class AdsSyncService:
    def __init__(self, fb_client: FacebookClient) -> None:
        self._fb = fb_client
        self._accounts = AdAccountRepository()
        self._campaigns = CampaignRepository()
        self._insights = InsightRepository()
        self._runs = SyncRunRepository()

    def sync_all_accounts(
        self,
        date_from: date,
        date_to: date,
        triggered_by: str = SyncTrigger.SCHEDULER,
    ) -> list[SyncRun]:
        accounts = self._accounts.get_all_active()
        results = []
        for account in accounts:
            run = self.sync_account(account.id, date_from, date_to, triggered_by)
            results.append(run)
        return results

    def sync_account(
        self,
        account_id: str,
        date_from: date,
        date_to: date,
        triggered_by: str = SyncTrigger.SCHEDULER,
    ) -> SyncRun:
        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise SyncError(f"Ad account not found: {account_id}")

        if self._runs.get_running(account_id) is not None:
            logger.info("sync_skipped", account_id=account_id, reason="already_running")
            raise SyncError("Sync already running for this account.")

        run = SyncRun(
            started_at=utcnow(),
            status=SyncStatus.RUNNING,
            ad_account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            triggered_by=triggered_by,
        )
        self._runs.save(run)
        logger.info("sync_started", account_id=account_id, date_from=str(date_from), date_to=str(date_to))

        upserted = 0
        failed_levels: list[str] = []

        for level in [InsightLevel.CAMPAIGN, InsightLevel.ADSET, InsightLevel.AD]:
            try:
                upserted += self._sync_level(account, level.value, date_from, date_to)
            except FacebookError as exc:
                logger.warning("sync_level_failed", level=level.value, error=str(exc))
                failed_levels.append(level.value)

        if failed_levels and upserted == 0:
            run.status = SyncStatus.FAILED
            run.error_message = f"All levels failed: {', '.join(failed_levels)}"
        elif failed_levels:
            run.status = SyncStatus.PARTIAL
            run.error_message = f"Failed levels: {', '.join(failed_levels)}"
        else:
            run.status = SyncStatus.SUCCESS

        run.finished_at = utcnow()
        run.records_upserted = upserted
        self._runs.save(run)

        account.last_synced_at = utcnow()
        self._accounts.save(account)

        logger.info("sync_finished", account_id=account_id, status=run.status, upserted=upserted)
        return run

    def _sync_level(
        self, account: object, level: str, date_from: date, date_to: date
    ) -> int:
        fb_account_id = account.fb_account_id  # type: ignore[union-attr]
        raw_insights = self._fb.get_insights(
            fb_account_id, str(date_from), str(date_to), level=level
        )
        count = 0
        for raw in raw_insights:
            insight = self._map_insight(raw, level, account.id)  # type: ignore[union-attr]
            self._insights.upsert(insight)
            count += 1
        return count

    def _map_insight(self, raw: dict[str, object], level: str, ad_account_id: str) -> Insight:
        from adsreport.core.time import utcnow as _now
        import json

        def cents(val: object) -> int:
            try:
                return round(float(str(val)) * 100)
            except (ValueError, TypeError):
                return 0

        def get_action(actions: list[dict[str, object]], action_type: str) -> int:
            for a in actions or []:
                if a.get("action_type") == action_type:
                    try:
                        return int(str(a.get("value", 0)))
                    except ValueError:
                        return 0
            return 0

        actions = raw.get("actions") or []
        spend = float(str(raw.get("spend", 0)))
        impressions = int(str(raw.get("impressions", 0)))

        entity_id_map = {
            "campaign": raw.get("campaign_id"),
            "adset": raw.get("adset_id"),
            "ad": raw.get("ad_id"),
            "account": ad_account_id,
        }
        entity_id = str(entity_id_map.get(level) or ad_account_id)

        return Insight(
            date=date.fromisoformat(str(raw.get("date_start", ""))),
            level=level,
            entity_id=entity_id,
            ad_account_id=ad_account_id,
            impressions=impressions,
            clicks=int(str(raw.get("clicks", 0))),
            spend_cents=cents(spend),
            reach=int(str(raw.get("reach", 0))),
            frequency=float(str(raw.get("frequency", 0))),
            ctr=float(str(raw.get("ctr", 0))),
            cpc_cents=cents(raw.get("cpc", 0)),
            cpm_cents=cents(raw.get("cpm", 0)),
            conversions=get_action(actions, "offsite_conversion.fb_pixel_custom"),
            leads=get_action(actions, "lead"),
            purchase_value_cents=cents(
                next((a.get("value", 0) for a in (raw.get("action_values") or [])
                      if a.get("action_type") == "offsite_conversion.fb_pixel_purchase"), 0)
            ),
            roas=spend and (
                float(str(next((a.get("value", 0) for a in (raw.get("action_values") or [])
                                if a.get("action_type") == "offsite_conversion.fb_pixel_purchase"), 0)))
                / spend
            ) or 0.0,
            raw_actions_json=json.dumps(actions) if actions else None,
            synced_at=_now(),
        )
