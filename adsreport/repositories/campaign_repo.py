from __future__ import annotations

from sqlalchemy import select

from adsreport.db.models.campaign import Campaign
from adsreport.repositories.base import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    model_class = Campaign

    def get_by_fb_id(self, fb_campaign_id: str) -> Campaign | None:
        stmt = select(Campaign).where(Campaign.fb_campaign_id == fb_campaign_id)
        return self.session.scalar(stmt)

    def get_by_account(self, ad_account_id: str) -> list[Campaign]:
        stmt = select(Campaign).where(Campaign.ad_account_id == ad_account_id)
        return list(self.session.scalars(stmt).all())

    def get_names_by_fb_ids(self, fb_campaign_ids: list[str]) -> dict[str, str]:
        if not fb_campaign_ids:
            return {}
        stmt = select(Campaign.fb_campaign_id, Campaign.name).where(
            Campaign.fb_campaign_id.in_(fb_campaign_ids)
        )
        return {fb_id: name for fb_id, name in self.session.execute(stmt)}

    def upsert_from_fb(self, fb_data: dict[str, object], ad_account_id: str) -> Campaign:
        fb_id = str(fb_data["id"])
        campaign = self.get_by_fb_id(fb_id)
        if campaign is None:
            campaign = Campaign(fb_campaign_id=fb_id, ad_account_id=ad_account_id)
        campaign.name = str(fb_data.get("name", ""))
        campaign.objective = str(fb_data.get("objective", ""))
        campaign.status = str(fb_data.get("status", campaign.status or "ACTIVE"))
        campaign.effective_status = str(
            fb_data.get("effective_status", campaign.effective_status or "ACTIVE")
        )
        return self.save(campaign)
