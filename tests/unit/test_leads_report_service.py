from __future__ import annotations

from typing import TYPE_CHECKING, Any

from adsreport.services.leads_report_service import LeadsReportService

if TYPE_CHECKING:
    from pathlib import Path


class FakeFacebookClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def get_insights(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        return [
            {
                "campaign_name": "iphone",
                "adset_name": "REELS - Cadastros — Cidades",
                "ad_name": "Reels 03",
                "region": "São Paulo (state)",
                "impressions": "7349",
                "actions": [{"action_type": "lead", "value": "9"}],
                "cost_per_action_type": [{"action_type": "lead", "value": "27.02821102"}],
                "spend": "243.25389919",
                "cpm": "33.10027204",
                "date_start": "2026-05-01",
                "date_stop": "2026-05-31",
            }
        ]


def test_fetch_monthly_maps_facebook_insights_to_ads_manager_columns() -> None:
    fb = FakeFacebookClient()
    service = LeadsReportService(fb)  # type: ignore[arg-type]

    rows = service.fetch_monthly("act_123", "2026-05-01", "2026-05-31")

    assert fb.calls[0]["level"] == "ad"
    assert fb.calls[0]["breakdowns"] == ["region"]
    assert fb.calls[0]["action_breakdowns"] == ["action_type"]
    assert fb.calls[0]["time_increment"] == "all_days"

    row = rows[0].to_ads_manager_dict()
    assert row == {
        "Nome da campanha": "iphone",
        "Nome do conjunto de anúncios": "REELS - Cadastros — Cidades",
        "Nome do anúncio": "Reels 03",
        "Região": "São Paulo (state)",
        "Impressões": 7349,
        "Tipo de resultado": "Leads (formulário)",
        "Resultados": 9,
        "Custo por resultado": 27.02821102,
        "Valor usado (BRL)": 243.25389919,
        "CPM (custo por 1.000 impressões)": 33.10027204,
        "Início dos relatórios": "2026-05-01",
        "Encerramento dos relatórios": "2026-05-31",
    }


def test_export_csv_writes_utf8_sig_file(tmp_path: Path) -> None:
    fb = FakeFacebookClient()
    service = LeadsReportService(fb)  # type: ignore[arg-type]
    rows = service.fetch_monthly("123", "2026-05-01", "2026-05-31")
    output = tmp_path / "leads.csv"

    service.export_csv(rows, output)

    content = output.read_text(encoding="utf-8-sig")
    assert "Nome da campanha" in content
    assert "São Paulo (state)" in content
