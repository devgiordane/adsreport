"""Thin wrapper over facebook-business SDK.

All Facebook API calls go through this class — never directly from callbacks or services.
"""

from __future__ import annotations

from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from adsreport.core.errors import FacebookError, FacebookRateLimitError
from adsreport.core.logging import get_logger

logger = get_logger(__name__)


class FacebookClient:
    def __init__(self, app_id: str, app_secret: str, access_token: str, api_version: str = "v21.0") -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.api_version = api_version
        self._api = self._init_api()

    def _init_api(self) -> Any:
        try:
            from facebook_business.api import FacebookAdsApi

            return FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=self.access_token,
                api_version=self.api_version,
            )
        except Exception as exc:
            raise FacebookError(f"Failed to initialize Facebook API: {exc}") from exc

    def get_me(self) -> dict[str, Any]:
        try:
            from facebook_business.adobjects.user import User

            return dict(User(fbid="me").api_get(fields=["id", "name"]))
        except Exception as exc:
            self._handle_exc(exc)

    def get_ad_accounts(self) -> list[dict[str, Any]]:
        try:
            from facebook_business.adobjects.user import User

            user = User(fbid="me")
            accounts = user.get_ad_accounts(
                fields=["id", "name", "currency", "timezone_name", "account_status"]
            )
            return [dict(a) for a in accounts]
        except Exception as exc:
            self._handle_exc(exc)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        reraise=True,
    )
    def get_campaigns(self, account_id: str) -> list[dict[str, Any]]:
        try:
            from facebook_business.adobjects.adaccount import AdAccount

            account = AdAccount(f"act_{account_id}" if not account_id.startswith("act_") else account_id)
            campaigns = account.get_campaigns(
                fields=["id", "name", "objective", "status", "effective_status",
                        "daily_budget", "lifetime_budget", "start_time", "stop_time"]
            )
            return [dict(c) for c in campaigns]
        except Exception as exc:
            self._handle_exc(exc)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        reraise=True,
    )
    def get_insights(
        self,
        account_id: str,
        date_from: str,
        date_to: str,
        level: str = "campaign",
    ) -> list[dict[str, Any]]:
        try:
            from facebook_business.adobjects.adaccount import AdAccount

            acct_id = f"act_{account_id}" if not account_id.startswith("act_") else account_id
            account = AdAccount(acct_id)
            params = {
                "level": level,
                "time_range": {"since": date_from, "until": date_to},
                "time_increment": 1,
                "fields": [
                    "date_start", "campaign_id", "adset_id", "ad_id",
                    "impressions", "clicks", "spend", "reach", "frequency",
                    "ctr", "cpc", "cpm", "actions", "action_values",
                ],
            }
            cursor = account.get_insights(params=params)
            results: list[dict[str, Any]] = []
            for page in cursor:
                results.extend([dict(r) for r in page])
            return results
        except Exception as exc:
            self._handle_exc(exc)

    def _handle_exc(self, exc: Exception) -> None:
        msg = str(exc)
        if "rate limit" in msg.lower() or "17" in msg:
            raise FacebookRateLimitError(msg) from exc
        if "190" in msg or "token" in msg.lower():
            raise FacebookError(f"Access token error: {msg}", status_code=190) from exc
        raise FacebookError(msg) from exc
