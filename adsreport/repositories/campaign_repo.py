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

    def upsert_from_fb(self, fb_data: dict[str, object], ad_account_id: str) -> Campaign:
        fb_id = str(fb_data["id"])
        campaign = self.get_by_fb_id(fb_id)
        if campaign is None:
            campaign = Campaign(fb_campaign_id=fb_id, ad_account_id=ad_account_id)
        campaign.name = str(fb_data.get("name", ""))
        campaign.objective = str(fb_data.get("objective", ""))
        campaign.status = str(fb_data.get("status", "ACTIVE"))
        campaign.effective_status = str(fb_data.get("effective_status", "ACTIVE"))
        return self.save(campaign)
