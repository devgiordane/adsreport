"""Lead report extraction from Facebook Ads Insights."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from adsreport.services.facebook_client import FacebookClient


LEAD_ACTION_TYPES = (
    "lead",
    "onsite_conversion.lead_grouped",
    "offsite_conversion.fb_pixel_lead",
    "leadgen_grouped",
)

LEADS_REPORT_FIELDS = (
    "date_start",
    "date_stop",
    "campaign_id",
    "campaign_name",
    "adset_id",
    "adset_name",
    "ad_id",
    "ad_name",
    "impressions",
    "spend",
    "cpm",
    "actions",
    "cost_per_action_type",
)


@dataclass(frozen=True)
class LeadsReportRow:
    campaign_name: str
    adset_name: str
    ad_name: str
    breakdown_value: str
    impressions: int
    result_type: str
    results: int
    cost_per_result: float
    spend: float
    cpm: float
    date_start: str
    date_stop: str

    def to_ads_manager_dict(self, breakdown_label: str = "Região") -> dict[str, str | int | float]:
        return {
            "Nome da campanha": self.campaign_name,
            "Nome do conjunto de anúncios": self.adset_name,
            "Nome do anúncio": self.ad_name,
            breakdown_label: self.breakdown_value,
            "Impressões": self.impressions,
            "Tipo de resultado": self.result_type,
            "Resultados": self.results,
            "Custo por resultado": self.cost_per_result,
            "Valor usado (BRL)": self.spend,
            "CPM (custo por 1.000 impressões)": self.cpm,
            "Início dos relatórios": self.date_start,
            "Encerramento dos relatórios": self.date_stop,
        }


def _to_float(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _actions(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [
        {str(key): item_value for key, item_value in item.items()}
        for item in value
        if isinstance(item, dict)
    ]


def _first_action_value(actions: list[dict[str, object]]) -> tuple[str, object]:
    for action_type in LEAD_ACTION_TYPES:
        for action in actions:
            if action.get("action_type") == action_type:
                return action_type, action.get("value", 0)
    return "", 0


class LeadsReportService:
    def __init__(self, fb_client: FacebookClient) -> None:
        self._fb = fb_client

    def fetch_monthly(
        self,
        account_id: str,
        date_from: str,
        date_to: str,
        breakdown: str = "region",
    ) -> list[LeadsReportRow]:
        raw_rows = self._fb.get_insights(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            level="ad",
            fields=LEADS_REPORT_FIELDS,
            breakdowns=[breakdown],
            action_breakdowns=["action_type"],
            time_increment="all_days",
        )
        rows = [self._map_row(raw, breakdown) for raw in raw_rows]
        return sorted(rows, key=lambda row: (row.campaign_name, row.adset_name, row.ad_name, row.breakdown_value))

    def export_csv(
        self,
        rows: Iterable[LeadsReportRow],
        output_path: Path,
        breakdown_label: str = "Região",
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(LeadsReportRow("", "", "", "", 0, "", 0, 0.0, 0.0, 0.0, "", "").to_ads_manager_dict(breakdown_label))
        with output_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row.to_ads_manager_dict(breakdown_label))

    def _map_row(self, raw: dict[str, Any], breakdown: str) -> LeadsReportRow:
        actions = _actions(raw.get("actions"))
        cost_actions = _actions(raw.get("cost_per_action_type"))
        action_type, result_value = _first_action_value(actions)
        _, cost_value = _first_action_value(cost_actions)

        return LeadsReportRow(
            campaign_name=str(raw.get("campaign_name") or ""),
            adset_name=str(raw.get("adset_name") or ""),
            ad_name=str(raw.get("ad_name") or ""),
            breakdown_value=str(raw.get(breakdown) or ""),
            impressions=_to_int(raw.get("impressions", 0)),
            result_type=_result_type_label(action_type),
            results=_to_int(result_value),
            cost_per_result=_to_float(cost_value),
            spend=_to_float(raw.get("spend", 0)),
            cpm=_to_float(raw.get("cpm", 0)),
            date_start=str(raw.get("date_start") or ""),
            date_stop=str(raw.get("date_stop") or ""),
        )


def _result_type_label(action_type: str) -> str:
    if action_type in LEAD_ACTION_TYPES:
        return "Leads (formulário)"
    return action_type
