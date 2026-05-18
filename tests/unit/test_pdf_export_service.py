from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

import pytest

from adsreport.i18n import set_locale
from adsreport.services.pdf_export_service import (
    PDFExportService,
    PDFRendererUnavailableError,
    PDFReportContext,
)


class _Summary:
    spend_cents = 123456
    leads = 42
    cost_per_lead_cents = 2939
    ctr = 4.25
    clicks = 980
    impressions = 23000
    reach = 0
    cpm_cents = 5700
    cpc_cents = 126


@dataclass
class _Row:
    name: str
    spend_cents: int = 10000
    impressions: int = 1000
    clicks: int = 50
    ctr: float = 5.0
    leads: int = 20
    cost_per_lead_cents: int = 500


@dataclass
class _Report:
    summary: object = field(default_factory=_Summary)
    prev_summary: object = field(default_factory=_Summary)
    top_campaigns: list[object] = field(default_factory=lambda: [_Row("Launch Campaign With A Very Long Name")])
    top_adsets: list[object] = field(default_factory=list)


def _context() -> PDFReportContext:
    return PDFReportContext(
        account_names=["Client Account"],
        date_from=date(2026, 5, 1),
        date_to=date(2026, 5, 18),
        generated_at=datetime(2026, 5, 18, 10, 30),
        currency="BRL",
        data_freshness=datetime(2026, 5, 18, 9, 0),
        locale="en-US",
    )


def test_render_dashboard_html_contains_report_context_and_no_browser_artifacts() -> None:
    set_locale("en-US")

    html = PDFExportService().render_dashboard_html(_Report(), _context())

    assert "Ads Performance Report" in html
    assert "Client Account" in html
    assert "2026-05-01 - 2026-05-18" in html
    assert "Launch Campaign With A Very Long Name" in html
    assert "dashboard-export-pdf-btn" not in html
    assert "window.print" not in html


def test_generate_dashboard_pdf_returns_reportlab_pdf_and_descriptive_filename() -> None:
    set_locale("en-US")

    result = PDFExportService().generate_dashboard_pdf(_Report(), _context())

    assert result.content.startswith(b"%PDF")
    assert result.content_type == "application/pdf"
    assert result.filename == "adsreport-client-account-2026-05-01-2026-05-18.pdf"


def test_generate_dashboard_pdf_raises_when_styled_renderer_missing(monkeypatch) -> None:
    set_locale("en-US")

    monkeypatch.setattr(PDFExportService, "_reportlab_pdf", lambda *args, **kwargs: None)

    with pytest.raises(PDFRendererUnavailableError, match="ReportLab is required"):
        PDFExportService().generate_dashboard_pdf(_Report(), _context())


def test_minimal_pdf_uses_safe_wrapping_and_winansi_encoding() -> None:
    from adsreport.services.pdf_export_service import _minimal_pdf

    content = _minimal_pdf("Relatorio com acentos: João, São Luís, anúncios.\n" * 80)

    assert content.startswith(b"%PDF")
    assert b"/Encoding /WinAnsiEncoding" in content
    assert b"Jo\xe3o" in content
    assert b"Tj T* ()" not in content
