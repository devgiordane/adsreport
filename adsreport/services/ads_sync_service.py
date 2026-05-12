"""Incremental sync orchestrator for Facebook Ads data."""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING

from adsreport.constants import InsightLevel, SyncStatus, SyncTrigger
from adsreport.core.errors import FacebookError, SyncError
from adsreport.core.logging import get_logger
from adsreport.core.time import utcnow
from adsreport.db.models.insight import Insight
from adsreport.db.models.sync_run import SyncRun
from adsreport.db.session import get_session
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.repositories.adset_repo import AdSetRepository
from adsreport.repositories.campaign_repo import CampaignRepository
from adsreport.repositories.insight_repo import InsightRepository
from adsreport.repositories.sync_run_repo import SyncRunRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from adsreport.db.models.ad_account import AdAccount
    from adsreport.services.facebook_client import FacebookClient

logger = get_logger(__name__)

_PURCHASE_ACTION = "offsite_conversion.fb_pixel_purchase"


def _to_float(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _to_cents(value: object) -> int:
    return round(_to_float(value) * 100)


def _actions(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [
        {str(key): item_value for key, item_value in item.items()}
        for item in value
        if isinstance(item, dict)
    ]


def _action_value(actions: list[dict[str, object]], action_type: str) -> object:
    for action in actions:
        if action.get("action_type") == action_type:
            return action.get("value", 0)
    return 0


class AdsSyncService:
    def __init__(self, fb_client: FacebookClient, session: Session | None = None) -> None:
        self._fb = fb_client
        self._owns_session = session is None
        self._session = session or get_session()
        self._accounts = AdAccountRepository(self._session)
        self._adsets = AdSetRepository(self._session)
        self._campaigns = CampaignRepository(self._session)
        self._insights = InsightRepository(self._session)
        self._runs = SyncRunRepository(self._session)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> AdsSyncService:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if exc_type is not None:
            self._session.rollback()
        self.close()

    def sync_all_accounts(
        self,
        date_from: date,
        date_to: date,
        triggered_by: str = SyncTrigger.SCHEDULER,
    ) -> list[SyncRun]:
        accounts = self._accounts.get_sync_enabled()
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
        self, account: AdAccount, level: str, date_from: date, date_to: date
    ) -> int:
        fb_account_id = account.fb_account_id
        raw_insights = self._fb.get_insights(
            fb_account_id, str(date_from), str(date_to), level=level
        )
        count = 0
        synced_metadata: set[tuple[str, str]] = set()
        for raw in raw_insights:
            self._upsert_metadata(raw, account.id, synced_metadata)
            insight = self._map_insight(raw, level, account.id)
            self._insights.upsert(insight)
            count += 1
        return count

    def _upsert_metadata(
        self,
        raw: dict[str, object],
        ad_account_id: str,
        synced_metadata: set[tuple[str, str]],
    ) -> None:
        campaign_fb_id = str(raw.get("campaign_id") or "")
        if campaign_fb_id and ("campaign", campaign_fb_id) not in synced_metadata:
            self._campaigns.upsert_from_fb(
                {
                    "id": campaign_fb_id,
                    "name": raw.get("campaign_name") or campaign_fb_id,
                },
                ad_account_id,
            )
            synced_metadata.add(("campaign", campaign_fb_id))

        adset_fb_id = str(raw.get("adset_id") or "")
        if not adset_fb_id or not campaign_fb_id or ("adset", adset_fb_id) in synced_metadata:
            return

        campaign = self._campaigns.get_by_fb_id(campaign_fb_id)
        if campaign is None:
            return
        self._adsets.upsert_from_insight(
            adset_fb_id,
            str(raw.get("adset_name") or adset_fb_id),
            campaign.id,
            ad_account_id,
        )
        synced_metadata.add(("adset", adset_fb_id))

    def _map_insight(self, raw: dict[str, object], level: str, ad_account_id: str) -> Insight:
        actions = _actions(raw.get("actions"))
        action_values = _actions(raw.get("action_values"))
        spend = _to_float(raw.get("spend", 0))
        purchase_value = _to_float(_action_value(action_values, _PURCHASE_ACTION))
        roas = purchase_value / spend if spend > 0 else 0.0

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
            impressions=_to_int(raw.get("impressions", 0)),
            clicks=_to_int(raw.get("clicks", 0)),
            spend_cents=_to_cents(raw.get("spend", 0)),
            reach=_to_int(raw.get("reach", 0)),
            frequency=_to_float(raw.get("frequency", 0)),
            ctr=_to_float(raw.get("ctr", 0)),
            cpc_cents=_to_cents(raw.get("cpc", 0)),
            cpm_cents=_to_cents(raw.get("cpm", 0)),
            conversions=_to_int(_action_value(actions, "offsite_conversion.fb_pixel_custom")),
            leads=_to_int(_action_value(actions, "lead")),
            purchase_value_cents=_to_cents(purchase_value),
            roas=roas,
            raw_actions_json=json.dumps(actions) if actions else None,
            synced_at=utcnow(),
        )
