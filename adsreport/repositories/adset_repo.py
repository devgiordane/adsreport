from __future__ import annotations

from sqlalchemy import select

from adsreport.db.models.adset import AdSet
from adsreport.repositories.base import BaseRepository


class AdSetRepository(BaseRepository[AdSet]):
    model_class = AdSet

    def get_by_fb_id(self, fb_adset_id: str) -> AdSet | None:
        stmt = select(AdSet).where(AdSet.fb_adset_id == fb_adset_id)
        return self.session.scalar(stmt)

    def get_names_by_fb_ids(self, fb_adset_ids: list[str]) -> dict[str, str]:
        if not fb_adset_ids:
            return {}
        stmt = select(AdSet.fb_adset_id, AdSet.name).where(AdSet.fb_adset_id.in_(fb_adset_ids))
        return {fb_id: name for fb_id, name in self.session.execute(stmt)}

    def upsert_from_insight(
        self,
        fb_adset_id: str,
        name: str,
        campaign_id: str,
        ad_account_id: str,
    ) -> AdSet:
        adset = self.get_by_fb_id(fb_adset_id)
        if adset is None:
            adset = AdSet(
                fb_adset_id=fb_adset_id,
                campaign_id=campaign_id,
                ad_account_id=ad_account_id,
                name=name or fb_adset_id,
            )
        adset.name = name or adset.name or fb_adset_id
        adset.campaign_id = campaign_id
        adset.ad_account_id = ad_account_id
        return self.save(adset)
