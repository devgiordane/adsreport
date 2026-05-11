"""Import all models so SQLAlchemy metadata is populated before create_all()."""

from adsreport.db.models.ad import Ad
from adsreport.db.models.ad_account import AdAccount
from adsreport.db.models.adset import AdSet
from adsreport.db.models.audit_log import AuditLog
from adsreport.db.models.campaign import Campaign
from adsreport.db.models.insight import Insight
from adsreport.db.models.settings import AppSetting
from adsreport.db.models.sync_run import SyncRun
from adsreport.db.models.user import User

__all__ = [
    "Ad",
    "AdAccount",
    "AdSet",
    "AuditLog",
    "Campaign",
    "Insight",
    "AppSetting",
    "SyncRun",
    "User",
]
