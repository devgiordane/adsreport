"""Server-side PDF report generation for dashboard exports."""

from __future__ import annotations

import base64
import html
import re
import textwrap
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

from adsreport.core.time import format_currency, format_number, format_percent
from adsreport.i18n import t

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import date, datetime

    import plotly.graph_objects as go

    from adsreport.services.report_service import ReportData


@dataclass(frozen=True)
class PDFReportContext:
    account_names: list[str]
    date_from: date
    date_to: date
    generated_at: datetime
    currency: str = "BRL"
    data_freshness: datetime | None = None
    locale: str = "pt-BR"

    @property
    def account_label(self) -> str:
        if not self.account_names:
            return t("pdf.account.all")
        return ", ".join(self.account_names)

    @property
    def period_label(self) -> str:
        return f"{self.date_from.isoformat()} - {self.date_to.isoformat()}"


@dataclass(frozen=True)
class PDFExportResult:
    content: bytes
    filename: str
    content_type: str = "application/pdf"


class PDFRendererUnavailableError(RuntimeError):
    """Raised when the styled PDF renderer is not installed in the runtime."""


class PDFExportService:
    """Build a branded PDF from report data without printing the browser page."""

    def generate_dashboard_pdf(
        self,
        report: ReportData,
        context: PDFReportContext,
        timeseries_figure: go.Figure | None = None,
        breakdown_figure: go.Figure | None = None,
    ) -> PDFExportResult:
        reportlab_pdf = self._reportlab_pdf(report, context, timeseries_figure, breakdown_figure)
        if reportlab_pdf is None:
            raise PDFRendererUnavailableError(
                "ReportLab is required to generate styled dashboard PDFs. "
                "Install project dependencies and restart the AdsReport server."
            )
        return PDFExportResult(
            content=reportlab_pdf,
            filename=self.filename(context),
        )

    def render_dashboard_html(
        self,
        report: ReportData,
        context: PDFReportContext,
        timeseries_figure: go.Figure | None = None,
        breakdown_figure: go.Figure | None = None,
    ) -> str:
        summary = report.summary
        rows = self._campaign_rows(report.top_campaigns, context.currency)
        adset_rows = self._campaign_rows(report.top_adsets, context.currency)
        generated = context.generated_at.strftime("%Y-%m-%d %H:%M")
        freshness = (
            context.data_freshness.strftime("%Y-%m-%d %H:%M")
            if context.data_freshness is not None
            else t("pdf.data_freshness.unknown")
        )

        timeseries = self._figure_section(timeseries_figure, t("dashboard.chart.timeseries.title"))
        breakdown = self._figure_section(breakdown_figure, t("dashboard.chart.breakdown.title"))
        adsets = ""
        if adset_rows:
            adsets = self._table_section(t("dashboard.table.top_adsets"), adset_rows)

        return f"""<!doctype html>
<html lang="{html.escape(context.locale)}">
<head>
  <meta charset="utf-8">
  <title>{html.escape(t("pdf.title"))}</title>
  <style>{self._css()}</style>
</head>
<body>
  <header class="report-header">
    <div>
      <p class="eyebrow">AdsReport</p>
      <h1>{html.escape(t("pdf.title"))}</h1>
      <p class="subtitle">{html.escape(t("pdf.subtitle"))}</p>
    </div>
    <div class="report-meta">
      <strong>{html.escape(t("pdf.generated_at"))}</strong>
      <span>{html.escape(generated)}</span>
    </div>
  </header>

  <section class="context-grid">
    <div><span>{html.escape(t("pdf.account"))}</span><strong>{html.escape(context.account_label)}</strong></div>
    <div><span>{html.escape(t("pdf.period"))}</span><strong>{html.escape(context.period_label)}</strong></div>
    <div><span>{html.escape(t("pdf.data_freshness"))}</span><strong>{html.escape(freshness)}</strong></div>
  </section>

  <section class="kpi-grid">
    {self._kpi(t("dashboard.kpi.spend"), format_currency(summary.spend_cents, context.currency))}
    {self._kpi(t("dashboard.kpi.leads"), format_number(summary.leads))}
    {self._kpi(t("dashboard.kpi.cost_per_lead"), format_currency(summary.cost_per_lead_cents, context.currency))}
    {self._kpi(t("dashboard.kpi.ctr"), format_percent(summary.ctr))}
    {self._kpi(t("dashboard.kpi.clicks"), format_number(summary.clicks))}
    {self._kpi(t("dashboard.kpi.impressions"), format_number(summary.impressions))}
  </section>

  <section class="chart-row">
    {timeseries}
    {breakdown}
  </section>

  {self._table_section(t("dashboard.table.top_campaigns"), rows)}
  {adsets}

  <footer>
    {html.escape(t("pdf.footer"))}
  </footer>
</body>
</html>"""

    def filename(self, context: PDFReportContext) -> str:
        account = "all-accounts" if not context.account_names else "-".join(context.account_names[:2])
        safe_account = re.sub(r"[^A-Za-z0-9_-]+", "-", account).strip("-").lower() or "report"
        return f"adsreport-{safe_account}-{context.date_from.isoformat()}-{context.date_to.isoformat()}.pdf"

    def _figure_section(self, figure: go.Figure | None, title: str) -> str:
        image = self._figure_to_data_uri(figure) if figure is not None else None
        if image is None:
            return f"""<article class="chart-card">
  <h2>{html.escape(title)}</h2>
  <p class="chart-fallback">{html.escape(t("pdf.chart_unavailable"))}</p>
</article>"""
        return f"""<article class="chart-card">
  <h2>{html.escape(title)}</h2>
  <img src="{image}" alt="{html.escape(title)}">
</article>"""

    def _figure_to_data_uri(self, figure: go.Figure) -> str | None:
        try:
            image = figure.to_image(format="png", width=920, height=400, scale=2)
        except Exception:
            return None
        encoded = base64.b64encode(image).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def _campaign_rows(self, rows: Sequence[object], currency: str) -> list[dict[str, str]]:
        return [
            {
                "name": str(getattr(row, "name", "")),
                "spend": format_currency(int(getattr(row, "spend_cents", 0)), currency),
                "impressions": format_number(int(getattr(row, "impressions", 0))),
                "clicks": format_number(int(getattr(row, "clicks", 0))),
                "ctr": format_percent(float(getattr(row, "ctr", 0.0))),
                "leads": format_number(int(getattr(row, "leads", 0))),
                "cost_per_lead": format_currency(int(getattr(row, "cost_per_lead_cents", 0)), currency),
            }
            for row in rows
        ]

    def _table_section(self, title: str, rows: list[dict[str, str]]) -> str:
        if not rows:
            body = f"""<tr><td colspan="7" class="empty-cell">{html.escape(t("pdf.no_rows"))}</td></tr>"""
        else:
            body = "\n".join(
                f"""<tr>
  <td class="name">{html.escape(row["name"])}</td>
  <td>{html.escape(row["spend"])}</td>
  <td>{html.escape(row["impressions"])}</td>
  <td>{html.escape(row["clicks"])}</td>
  <td>{html.escape(row["ctr"])}</td>
  <td>{html.escape(row["leads"])}</td>
  <td>{html.escape(row["cost_per_lead"])}</td>
</tr>"""
                for row in rows
            )
        return f"""<section class="table-section">
  <h2>{html.escape(title)}</h2>
  <table>
    <thead>
      <tr>
        <th>{html.escape(t("dashboard.table.campaign"))}</th>
        <th>{html.escape(t("dashboard.table.spend"))}</th>
        <th>{html.escape(t("dashboard.table.impressions"))}</th>
        <th>{html.escape(t("dashboard.table.clicks"))}</th>
        <th>{html.escape(t("dashboard.table.ctr"))}</th>
        <th>{html.escape(t("dashboard.table.leads"))}</th>
        <th>{html.escape(t("dashboard.table.cost_per_lead"))}</th>
      </tr>
    </thead>
    <tbody>{body}</tbody>
  </table>
</section>"""

    def _kpi(self, label: str, value: str) -> str:
        return f"""<article class="kpi-card">
  <span>{html.escape(label)}</span>
  <strong>{html.escape(value)}</strong>
</article>"""

    def _html_to_pdf(self, html_doc: str) -> bytes:
        try:
            from weasyprint import HTML

            return cast("bytes", HTML(string=html_doc).write_pdf())
        except Exception:
            text = _html_text_content(html_doc)
            return _minimal_pdf(text[:3000])

    # ── ReportLab PDF ──────────────────────────────────────────────────────────

    def _reportlab_pdf(
        self,
        report: ReportData,
        context: PDFReportContext,
        timeseries_figure: go.Figure | None,
        breakdown_figure: go.Figure | None,
    ) -> bytes | None:
        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                HRFlowable,
                Image,
                KeepTogether,
                LongTable,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except Exception:
            return None

        # ── Design tokens ──────────────────────────────────────────────────────
        C_NAVY = colors.HexColor("#1E3A8A")
        C_BLUE_700 = colors.HexColor("#1D4ED8")
        C_BLUE = colors.HexColor("#2563EB")
        C_BLUE_400 = colors.HexColor("#60A5FA")
        C_BLUE_300 = colors.HexColor("#93C5FD")
        C_BLUE_200 = colors.HexColor("#BFDBFE")
        C_BLUE_100 = colors.HexColor("#DBEAFE")
        C_BLUE_50 = colors.HexColor("#EFF6FF")
        C_SLATE_900 = colors.HexColor("#0F172A")
        C_SLATE_700 = colors.HexColor("#334155")
        C_SLATE_500 = colors.HexColor("#64748B")
        C_SLATE_400 = colors.HexColor("#94A3B8")
        C_SLATE_300 = colors.HexColor("#CBD5E1")
        C_SLATE_200 = colors.HexColor("#E2E8F0")
        C_SLATE_100 = colors.HexColor("#F1F5F9")
        C_SLATE_50 = colors.HexColor("#F8FAFC")
        C_WHITE = colors.white
        C_SUCCESS = colors.HexColor("#059669")
        C_DANGER = colors.HexColor("#DC2626")

        PAGE_W = 186 * mm

        # ── Styles ─────────────────────────────────────────────────────────────
        base = getSampleStyleSheet()["BodyText"]

        def ps(name: str, **kw: Any) -> ParagraphStyle:
            return ParagraphStyle(name, parent=base, **kw)

        s_eyebrow = ps("Eyebrow", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_BLUE_200, spaceAfter=3)
        s_title = ps("BannerTitle", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=C_WHITE, spaceAfter=3)
        s_subtitle = ps("BannerSubtitle", fontSize=8.5, leading=11, textColor=C_BLUE_100)
        s_gen_label = ps("GenLabel", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_BLUE_200, spaceAfter=3, alignment=TA_RIGHT)
        s_gen_value = ps("GenValue", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=C_WHITE, alignment=TA_RIGHT)
        s_meta_label = ps("MetaLabel", fontName="Helvetica-Bold", fontSize=6, leading=7.5, textColor=C_SLATE_500, spaceAfter=3)
        s_meta_value = ps("MetaValue", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=C_SLATE_900)
        s_kpi_label = ps("KpiLabel", fontName="Helvetica-Bold", fontSize=6, leading=7.5, textColor=C_SLATE_500, spaceAfter=3)
        s_kpi_value = ps("KpiValue", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=C_SLATE_900, spaceAfter=2)
        s_kpi_delta = ps("KpiDelta", fontSize=6.5, leading=8, textColor=C_SLATE_400)
        s_section = ps("SectionTitle", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=C_SLATE_900)
        s_cell = ps("Cell", fontSize=7.5, leading=9.5, textColor=C_SLATE_700)
        s_cell_right = ps("CellRight", fontSize=7.5, leading=9.5, textColor=C_SLATE_700, alignment=TA_RIGHT)
        s_cell_bold = ps("CellBold", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=C_SLATE_900)
        s_th = ps("TH", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_WHITE, alignment=TA_RIGHT)
        s_th_left = ps("THLeft", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_WHITE)
        s_fallback = ps("Fallback", fontSize=8, leading=10, textColor=C_SLATE_500, alignment=TA_CENTER)
        s_footer = ps("Footer", fontSize=7, leading=9, textColor=C_SLATE_500, alignment=TA_RIGHT)
        s_funnel_label = ps("FunnelLabel", fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=C_SLATE_700)
        s_funnel_value = ps("FunnelValue", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=C_SLATE_900, alignment=TA_RIGHT)
        s_funnel_rate = ps("FunnelRate", fontSize=7, leading=9, textColor=C_SLATE_500, alignment=TA_RIGHT)
        s_spotlight_name = ps("SpotName", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=C_SLATE_900, spaceAfter=2)
        s_spotlight_sub = ps("SpotSub", fontSize=7.5, leading=9, textColor=C_SLATE_500)
        s_comp_th = ps("CompTH", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_WHITE)
        s_comp_th_right = ps("CompTHR", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_WHITE, alignment=TA_RIGHT)

        def p(text: object, style: ParagraphStyle = s_cell) -> Paragraph:
            return Paragraph(html.escape(str(text)), style)

        def p_raw(markup: str, style: ParagraphStyle = s_cell) -> Paragraph:
            return Paragraph(markup, style)

        # ── Delta helpers ──────────────────────────────────────────────────────
        # invert=True for cost metrics: lower value is better, so a decrease is green.
        def calc_delta(curr: float, prev: float, invert: bool = False) -> tuple[str, str] | None:
            if prev == 0:
                return None
            pct = (curr - prev) / prev * 100
            sign = "+" if pct >= 0 else ""
            is_good = (pct >= 0) if not invert else (pct <= 0)
            color_hex = "#059669" if is_good else "#DC2626"
            return f"{sign}{pct:.1f}%", color_hex

        def delta_paragraph(curr: float, prev: float, style: ParagraphStyle, invert: bool = False) -> Paragraph:
            info = calc_delta(curr, prev, invert=invert)
            if info is None:
                return Paragraph("—", style)
            text, color_hex = info
            return Paragraph(f'<font color="{color_hex}">{html.escape(text)}</font>', style)

        def kpi_cell(label: str, value: str, curr: float, prev: float, invert: bool = False) -> list[Paragraph]:
            items: list[Paragraph] = [p(label.upper(), s_kpi_label), p(value, s_kpi_value)]
            info = calc_delta(curr, prev, invert=invert)
            if info:
                text, color_hex = info
                vs = html.escape(t("pdf.vs_prev"))
                markup = f'<font color="{color_hex}">{html.escape(text)}</font> <font color="#94A3B8">{vs}</font>'
                items.append(p_raw(markup, s_kpi_delta))
            else:
                items.append(Paragraph("", s_kpi_delta))
            return items

        # ── Page number callback ───────────────────────────────────────────────
        def on_page(canvas: Any, doc: Any) -> None:
            page_num = canvas.getPageNumber()
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(C_SLATE_500)
            canvas.drawRightString(198 * mm, 7 * mm, f"Página {page_num}")
            if page_num > 1:
                canvas.setStrokeColor(C_BLUE)
                canvas.setLineWidth(2.5)
                canvas.line(12 * mm, A4[1] - 8 * mm, 198 * mm, A4[1] - 8 * mm)
            canvas.restoreState()

        def section_header(title_text: str) -> Table:
            bar = Table(
                [[Paragraph("", s_cell), p(title_text, s_section)]],
                colWidths=[4 * mm, PAGE_W - 4 * mm],
                rowHeights=[12 * mm],
            )
            bar.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), C_BLUE),
                    ("BACKGROUND", (1, 0), (1, 0), C_SLATE_100),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 0),
                    ("LEFTPADDING", (1, 0), (1, 0), 11),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, C_SLATE_200),
                ])
            )
            return bar

        story: list[object] = []
        generated = context.generated_at.strftime("%d/%m/%Y  %H:%M")
        freshness = (
            context.data_freshness.strftime("%d/%m/%Y  %H:%M")
            if context.data_freshness is not None
            else t("pdf.data_freshness.unknown")
        )
        summary = report.summary
        prev = report.prev_summary
        has_prev = prev.impressions > 0 or prev.clicks > 0 or prev.spend_cents > 0

        # ── 1. Header banner ──────────────────────────────────────────────────
        header = Table(
            [[
                [p("ADSREPORT", s_eyebrow), p(t("pdf.title"), s_title), p(t("pdf.subtitle"), s_subtitle)],
                [p(t("pdf.generated_at").upper(), s_gen_label), p(generated, s_gen_value)],
            ]],
            colWidths=[130 * mm, 56 * mm],
        )
        header.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), C_NAVY),
                ("BACKGROUND", (1, 0), (1, 0), C_BLUE_700),
                ("VALIGN", (0, 0), (0, 0), "BOTTOM"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 16),
                ("RIGHTPADDING", (0, 0), (0, 0), 10),
                ("LEFTPADDING", (1, 0), (1, 0), 14),
                ("RIGHTPADDING", (1, 0), (1, 0), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 16),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("LINEAFTER", (0, 0), (0, 0), 0.5, C_BLUE),
                ("LINEBELOW", (0, 0), (-1, -1), 3, C_BLUE),
            ])
        )
        story.extend([header, Spacer(1, 10)])

        # ── 2. Meta row ───────────────────────────────────────────────────────
        meta = Table(
            [[
                [p(t("pdf.account").upper(), s_meta_label), p(context.account_label, s_meta_value)],
                [p(t("pdf.period").upper(), s_meta_label), p(context.period_label, s_meta_value)],
                [p(t("pdf.data_freshness").upper(), s_meta_label), p(freshness, s_meta_value)],
            ]],
            colWidths=[72 * mm, 52 * mm, 62 * mm],
        )
        meta.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_SLATE_50),
                ("BOX", (0, 0), (-1, -1), 0.7, C_SLATE_300),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, C_SLATE_200),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                ("LINEABOVE", (0, 0), (-1, 0), 2.5, C_BLUE),
            ])
        )
        story.extend([meta, Spacer(1, 12)])

        # ── 3. KPI grid with period deltas ────────────────────────────────────
        # (label, formatted_value, current_raw, previous_raw, invert_color)
        # invert=True for cost metrics: lower cost = green.
        kpi_w = PAGE_W / 3
        kpis: list[tuple[str, str, float, float, bool]] = [
            (t("dashboard.kpi.spend"),         format_currency(summary.spend_cents, context.currency),         float(summary.spend_cents),         float(prev.spend_cents),         True),
            (t("dashboard.kpi.leads"),         format_number(summary.leads),                                   float(summary.leads),               float(prev.leads),               False),
            (t("dashboard.kpi.cost_per_lead"), format_currency(summary.cost_per_lead_cents, context.currency), float(summary.cost_per_lead_cents), float(prev.cost_per_lead_cents), True),
            (t("dashboard.kpi.ctr"),           format_percent(summary.ctr),                                    summary.ctr,                        prev.ctr,                        False),
            (t("dashboard.kpi.clicks"),        format_number(summary.clicks),                                  float(summary.clicks),              float(prev.clicks),              False),
            (t("dashboard.kpi.impressions"),   format_number(summary.impressions),                             float(summary.impressions),         float(prev.impressions),         False),
        ]
        kpi_rows = [
            [kpi_cell(label, value, curr, prev_val if has_prev else 0.0, inv) for label, value, curr, prev_val, inv in kpis[:3]],
            [kpi_cell(label, value, curr, prev_val if has_prev else 0.0, inv) for label, value, curr, prev_val, inv in kpis[3:]],
        ]
        kpi_table = Table(kpi_rows, colWidths=[kpi_w, kpi_w, kpi_w], rowHeights=[26 * mm, 26 * mm])
        kpi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_WHITE),
                ("BOX", (0, 0), (-1, -1), 0.7, C_SLATE_300),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, C_SLATE_200),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 13),
                ("RIGHTPADDING", (0, 0), (-1, -1), 13),
                ("LINEABOVE", (0, 0), (-1, 0), 3, C_BLUE),
            ])
        )
        story.extend([kpi_table, Spacer(1, 14)])

        # ── 4. Conversion funnel ──────────────────────────────────────────────
        has_reach = summary.reach > 0
        funnel_top = float(summary.reach if has_reach else summary.impressions)
        funnel_stages: list[tuple[str, int, str, float | None]] = []

        if has_reach:
            funnel_stages.append((
                t("pdf.funnel.reach"),
                summary.reach,
                "100%",
                None,
            ))
        funnel_stages.append((
            t("pdf.funnel.impressions"),
            summary.impressions,
            "100%" if not has_reach else (f"{summary.impressions / funnel_top * 100:.1f}%" if funnel_top > 0 else "—"),
            None,
        ))

        ctr_label = f"{summary.ctr:.2f}% {t('pdf.funnel.ctr')}"
        conv_label: str
        if summary.clicks > 0:
            conv_rate = summary.leads / summary.clicks * 100
            conv_label = f"{conv_rate:.1f}% {t('pdf.funnel.conv_rate')}"
        else:
            conv_label = "— " + t("pdf.funnel.conv_rate")

        funnel_stages.append((t("pdf.funnel.clicks"), summary.clicks, ctr_label, None))
        funnel_stages.append((t("pdf.funnel.leads"), summary.leads, conv_label, None))

        # Progressive bar colors: lightest → darkest blue as funnel narrows
        bar_palette = [C_BLUE_300, C_BLUE_400, C_BLUE, C_NAVY]
        if not has_reach:
            bar_palette = bar_palette[1:]

        BAR_MAX = 108 * mm

        def funnel_bar(stage_value: int, stage_idx: int) -> Table:
            ratio = (stage_value / funnel_top) if funnel_top > 0 else 0.0
            fill = max(ratio * BAR_MAX, 5 * mm) if stage_value > 0 else 2 * mm
            empty = BAR_MAX - fill
            bar_color = bar_palette[min(stage_idx, len(bar_palette) - 1)]
            inner = Table([["", ""]], colWidths=[fill, empty], rowHeights=[7 * mm])
            inner.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), bar_color),
                ("BACKGROUND", (1, 0), (1, 0), C_SLATE_100),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            return inner

        funnel_data = []
        for idx, (stage_name, stage_value, rate_str, _) in enumerate(funnel_stages):
            funnel_data.append([
                p(stage_name, s_funnel_label),
                funnel_bar(stage_value, idx),
                p(format_number(stage_value), s_funnel_value),
                p(rate_str, s_funnel_rate),
            ])

        # colWidths: label(35) + bar(108) + value(25) + rate(18) = 186mm
        funnel_table = Table(funnel_data, colWidths=[35 * mm, BAR_MAX, 27 * mm, 16 * mm])
        funnel_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_WHITE),
                ("BOX", (0, 0), (-1, -1), 0.7, C_SLATE_300),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, C_SLATE_200),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 11),
                ("LEFTPADDING", (1, 0), (1, -1), 0),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("LEFTPADDING", (2, 0), (3, -1), 6),
                ("RIGHTPADDING", (2, 0), (3, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(
            KeepTogether([
                section_header(t("pdf.funnel.title")),
                Spacer(1, 5),
                funnel_table,
                Spacer(1, 12),
            ])
        )

        # ── 5. Period comparison table ─────────────────────────────────────────
        if has_prev:
            # (label, curr_str, prev_str, curr_v, prev_v, invert_color)
            comp_metrics: list[tuple[str, str, str, float, float, bool]] = [
                (t("dashboard.kpi.impressions"),   format_number(summary.impressions),                             format_number(prev.impressions),                             float(summary.impressions),         float(prev.impressions),         False),
                (t("dashboard.kpi.clicks"),        format_number(summary.clicks),                                  format_number(prev.clicks),                                  float(summary.clicks),              float(prev.clicks),              False),
                (t("dashboard.kpi.ctr"),           format_percent(summary.ctr),                                    format_percent(prev.ctr),                                    summary.ctr,                        prev.ctr,                        False),
                (t("dashboard.kpi.spend"),         format_currency(summary.spend_cents, context.currency),         format_currency(prev.spend_cents, context.currency),         float(summary.spend_cents),         float(prev.spend_cents),         True),
                (t("dashboard.kpi.cpm"),           format_currency(summary.cpm_cents, context.currency),           format_currency(prev.cpm_cents, context.currency),           float(summary.cpm_cents),           float(prev.cpm_cents),           True),
                (t("dashboard.kpi.cpc"),           format_currency(summary.cpc_cents, context.currency),           format_currency(prev.cpc_cents, context.currency),           float(summary.cpc_cents),           float(prev.cpc_cents),           True),
                (t("dashboard.kpi.leads"),         format_number(summary.leads),                                   format_number(prev.leads),                                   float(summary.leads),               float(prev.leads),               False),
                (t("dashboard.kpi.cost_per_lead"), format_currency(summary.cost_per_lead_cents, context.currency), format_currency(prev.cost_per_lead_cents, context.currency), float(summary.cost_per_lead_cents), float(prev.cost_per_lead_cents), True),
            ]

            comp_header_row = [
                p(t("pdf.period_comparison.metric"), s_comp_th),
                p(t("pdf.period_comparison.current"), s_comp_th_right),
                p(t("pdf.period_comparison.previous"), s_comp_th_right),
                p(t("pdf.period_comparison.change"), s_comp_th_right),
            ]
            comp_data = [comp_header_row]
            for metric_label, curr_str, prev_str, curr_v, prev_v, inv in comp_metrics:
                comp_data.append([
                    p(metric_label, s_cell),
                    p(curr_str, s_cell_right),
                    p(prev_str, s_cell_right),
                    delta_paragraph(curr_v, prev_v, s_cell_right, invert=inv),
                ])

            # colWidths: metric(62) + current(40) + previous(40) + change(44) = 186mm
            comp_table = Table(comp_data, colWidths=[62 * mm, 40 * mm, 40 * mm, 44 * mm], repeatRows=1)
            comp_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_SLATE_50]),
                    ("BOX", (0, 0), (-1, -1), 0.7, C_SLATE_300),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, C_NAVY),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.4, C_SLATE_200),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(
                KeepTogether([
                    section_header(t("pdf.period_comparison.title")),
                    Spacer(1, 5),
                    comp_table,
                    Spacer(1, 12),
                ])
            )

        # ── 6. Charts ─────────────────────────────────────────────────────────
        for fig, title in [
            (timeseries_figure, t("dashboard.chart.timeseries.title")),
            (breakdown_figure, t("dashboard.chart.breakdown.title")),
        ]:
            chart = self._reportlab_chart_card(fig, Image, p, s_fallback)
            story.append(
                KeepTogether([
                    section_header(title),
                    Spacer(1, 5),
                    chart,
                    Spacer(1, 12),
                ])
            )

        # ── 7. Spotlight: best campaign ────────────────────────────────────────
        if report.top_campaigns:
            best = max(report.top_campaigns, key=lambda c: getattr(c, "leads", 0))
            subtitle_key = "pdf.spotlight.by_leads"
            if getattr(best, "leads", 0) == 0:
                best = max(report.top_campaigns, key=lambda c: getattr(c, "clicks", 0))
                subtitle_key = "pdf.spotlight.by_clicks"

            spot_metrics = [
                (t("dashboard.kpi.leads"),         format_number(int(getattr(best, "leads", 0)))),
                (t("dashboard.kpi.spend"),         format_currency(int(getattr(best, "spend_cents", 0)), context.currency)),
                (t("dashboard.kpi.cost_per_lead"), format_currency(int(getattr(best, "cost_per_lead_cents", 0)), context.currency)),
                (t("dashboard.kpi.ctr"),           format_percent(float(getattr(best, "ctr", 0.0)))),
            ]
            spot_col_w = (PAGE_W - 4 * mm) / len(spot_metrics)

            spot_kpi_data = [[
                [p(lbl.upper(), s_kpi_label), p(val, ps(f"SpotVal{i}", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=C_SLATE_900))]
                for i, (lbl, val) in enumerate(spot_metrics)
            ]]
            spot_kpi_table = Table(spot_kpi_data, colWidths=[spot_col_w] * len(spot_metrics), rowHeights=[18 * mm])
            spot_kpi_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), C_BLUE_50),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, C_BLUE_200),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ])
            )

            spot_content = Table(
                [
                    [[p(str(getattr(best, "name", "")), s_spotlight_name), p(t(subtitle_key), s_spotlight_sub)]],
                    [spot_kpi_table],
                ],
                colWidths=[PAGE_W - 4 * mm],
            )
            spot_content.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), C_WHITE),
                    ("TOPPADDING", (0, 0), (0, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 1), (0, 1), 0),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 0),
                    ("LEFTPADDING", (0, 1), (0, 1), 0),
                    ("RIGHTPADDING", (0, 1), (0, 1), 0),
                ])
            )

            spotlight = Table(
                [[Paragraph("", s_cell), spot_content]],
                colWidths=[4 * mm, PAGE_W - 4 * mm],
            )
            spotlight.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), C_BLUE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("BOX", (0, 0), (-1, -1), 0.7, C_SLATE_300),
                    ("LINEABOVE", (0, 0), (-1, 0), 2.5, C_BLUE),
                ])
            )

            story.append(
                KeepTogether([
                    section_header(t("pdf.spotlight.title")),
                    Spacer(1, 5),
                    spotlight,
                    Spacer(1, 12),
                ])
            )

        # ── 8. Campaign tables ─────────────────────────────────────────────────
        story.append(
            KeepTogether([
                section_header(t("dashboard.table.top_campaigns")),
                Spacer(1, 5),
            ])
        )
        story.append(
            self._reportlab_table(
                report.top_campaigns,
                context.currency,
                LongTable,
                TableStyle,
                p,
                s_th,
                s_th_left,
                s_cell_right,
            )
        )

        if report.top_adsets:
            story.extend([Spacer(1, 12)])
            story.append(
                KeepTogether([
                    section_header(t("dashboard.table.top_adsets")),
                    Spacer(1, 5),
                ])
            )
            story.append(
                self._reportlab_table(
                    report.top_adsets,
                    context.currency,
                    LongTable,
                    TableStyle,
                    p,
                    s_th,
                    s_th_left,
                    s_cell_right,
                )
            )

        # ── 9. Footer ──────────────────────────────────────────────────────────
        story.extend([
            Spacer(1, 14),
            HRFlowable(width="100%", thickness=0.5, color=C_SLATE_300),
            Spacer(1, 5),
            p(t("pdf.footer"), s_footer),
        ])

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=12 * mm,
            leftMargin=12 * mm,
            topMargin=14 * mm,
            bottomMargin=18 * mm,
            title=t("pdf.title"),
        )
        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        return buffer.getvalue()

    def _reportlab_chart_card(
        self,
        figure: go.Figure | None,
        image_cls: Callable[..., Any],
        paragraph_cls: Callable[..., Any],
        fallback_style: Any,
    ) -> object:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Table, TableStyle

        C_BLUE = colors.HexColor("#2563EB")
        C_SLATE_200 = colors.HexColor("#E2E8F0")

        image_uri = self._figure_to_data_uri(figure) if figure is not None else None
        content: object
        if image_uri:
            raw = base64.b64decode(image_uri.split(",", 1)[1])
            content = image_cls(BytesIO(raw), width=170 * mm, height=68 * mm)
        else:
            content = paragraph_cls(t("pdf.chart_unavailable"), fallback_style)

        card = Table([[content]], colWidths=[186 * mm])
        card.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, C_SLATE_200),
                ("LINEABOVE", (0, 0), (-1, 0), 2.5, C_BLUE),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        return card

    def _reportlab_table(
        self,
        rows: Sequence[object],
        currency: str,
        table_cls: Any,
        table_style_cls: Any,
        paragraph: Callable[..., Any],
        header_style: Any,
        header_left_style: Any,
        cell_right_style: Any,
    ) -> object:
        from reportlab.lib import colors
        from reportlab.lib.units import mm

        C_NAVY = colors.HexColor("#1E3A8A")
        C_WHITE = colors.white
        C_SLATE_50 = colors.HexColor("#F8FAFC")
        C_SLATE_200 = colors.HexColor("#E2E8F0")
        C_SLATE_300 = colors.HexColor("#CBD5E1")

        headers = [
            t("dashboard.table.campaign"),
            t("dashboard.table.spend"),
            t("dashboard.table.impressions"),
            t("dashboard.table.clicks"),
            t("dashboard.table.ctr"),
            t("dashboard.table.leads"),
            t("dashboard.table.cost_per_lead"),
        ]

        header_row = [paragraph(headers[0], header_left_style)] + [
            paragraph(h, header_style) for h in headers[1:]
        ]
        data = [header_row]

        for row in self._campaign_rows(rows, currency):
            data.append([
                paragraph(row["name"]),
                paragraph(row["spend"], cell_right_style),
                paragraph(row["impressions"], cell_right_style),
                paragraph(row["clicks"], cell_right_style),
                paragraph(row["ctr"], cell_right_style),
                paragraph(row["leads"], cell_right_style),
                paragraph(row["cost_per_lead"], cell_right_style),
            ])

        if len(data) == 1:
            data.append([paragraph(t("pdf.no_rows"))] + [""] * 6)

        table = table_cls(
            data,
            colWidths=[67 * mm, 22 * mm, 21 * mm, 17 * mm, 15 * mm, 14 * mm, 30 * mm],
            repeatRows=1,
        )
        table.setStyle(
            table_style_cls([
                ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_SLATE_50]),
                ("BOX", (0, 0), (-1, -1), 0.7, C_SLATE_300),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, C_NAVY),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, C_SLATE_200),
                ("LINEBEFORE", (1, 0), (1, -1), 0.4, C_SLATE_200),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ])
        )
        return table

    def _css(self) -> str:
        return """
@page { size: A4 portrait; margin: 14mm; @bottom-center { content: counter(page); color: #64748b; font-size: 9px; } }
* { box-sizing: border-box; }
body { color: #0f172a; font-family: Inter, Arial, sans-serif; font-size: 11px; line-height: 1.45; }
.report-header { align-items: flex-start; border-bottom: 2px solid #2563eb; display: flex; justify-content: space-between; padding-bottom: 12px; }
.eyebrow { color: #2563eb; font-size: 10px; font-weight: 800; letter-spacing: .08em; margin: 0 0 4px; text-transform: uppercase; }
h1 { font-size: 28px; line-height: 1.05; margin: 0; }
h2 { font-size: 13px; margin: 0 0 10px; }
.subtitle { color: #475569; margin: 6px 0 0; }
.report-meta { border: 1px solid #dbe3ef; border-radius: 8px; padding: 8px 10px; text-align: right; }
.report-meta span, .context-grid span, .kpi-card span { color: #64748b; display: block; font-size: 9px; text-transform: uppercase; }
.context-grid { display: grid; gap: 8px; grid-template-columns: 2fr 1fr 1fr; margin: 16px 0; }
.context-grid div, .kpi-card, .chart-card, .table-section { border: 1px solid #dbe3ef; border-radius: 8px; padding: 10px; }
.kpi-grid { display: grid; gap: 8px; grid-template-columns: repeat(3, 1fr); margin-bottom: 14px; }
.kpi-card { break-inside: avoid; }
.kpi-card strong { display: block; font-size: 18px; margin-top: 4px; }
.chart-row { display: grid; gap: 10px; grid-template-columns: 1fr; margin-bottom: 14px; }
.chart-card { break-inside: avoid; }
.chart-card img { display: block; max-width: 100%; width: 100%; }
.chart-fallback { color: #64748b; margin: 0; }
.table-section { break-inside: auto; margin-top: 12px; padding: 0; }
.table-section h2 { padding: 10px 10px 0; }
table { border-collapse: collapse; width: 100%; }
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th, td { border-top: 1px solid #e2e8f0; padding: 6px; text-align: right; vertical-align: top; }
th { background: #f8fafc; color: #475569; font-size: 8px; text-transform: uppercase; }
td.name, th:first-child { text-align: left; width: 34%; word-break: break-word; }
.empty-cell { color: #64748b; text-align: center; }
footer { border-top: 1px solid #dbe3ef; color: #64748b; font-size: 9px; margin-top: 18px; padding-top: 8px; }
"""


def _minimal_pdf(text: str) -> bytes:
    lines = _wrap_pdf_text(text)
    pages = [lines[i : i + 52] for i in range(0, len(lines), 52)] or [["AdsReport"]]
    page_object_ids = [3 + i * 2 for i in range(len(pages))]
    font_object_id = 3 + len(pages) * 2

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        (
            b"2 0 obj << /Type /Pages /Kids ["
            + b" ".join(f"{obj_id} 0 R".encode() for obj_id in page_object_ids)
            + f"] /Count {len(pages)} >> endobj\n".encode()
        ),
    ]
    for page_number, page_lines in enumerate(pages):
        page_object_id = page_object_ids[page_number]
        content_object_id = page_object_id + 1
        stream = _pdf_page_stream(page_lines)
        objects.extend(
            [
                (
                    f"{page_object_id} 0 obj << /Type /Page /Parent 2 0 R "
                    f"/MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_object_id} 0 R >> >> "
                    f"/Contents {content_object_id} 0 R >> endobj\n"
                ).encode(),
                (
                    f"{content_object_id} 0 obj << /Length {len(stream)} >> stream\n".encode()
                    + stream
                    + b"\nendstream endobj\n"
                ),
            ]
        )
    objects.append(
        (
            f"{font_object_id} 0 obj << /Type /Font /Subtype /Type1 "
            "/BaseFont /Helvetica /Encoding /WinAnsiEncoding >> endobj\n"
        ).encode()
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Root 1 0 R /Size {len(offsets)} >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(pdf)


def _wrap_pdf_text(text: str) -> list[str]:
    normalized = text.replace("\r", "\n")
    lines: list[str] = []
    for paragraph in normalized.splitlines():
        compact = re.sub(r"\s+", " ", paragraph).strip()
        if not compact:
            continue
        lines.extend(textwrap.wrap(compact, width=86, break_long_words=False, break_on_hyphens=False) or [compact])
    return lines


def _pdf_page_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("cp1252", "replace")


def _pdf_escape(text: str) -> str:
    cleaned = text.replace("\n", " ").replace("\r", " ")
    cleaned = "".join(char if char >= " " else " " for char in cleaned)
    return cleaned.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class _ReportTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"head", "style", "script"}:
            self._ignored_depth += 1
            return
        if tag in {"td", "th"}:
            self._chunks.append(" ")
        if tag in {"h1", "h2", "p", "div", "section", "article", "tr", "footer"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"head", "style", "script"} and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if tag in {"td", "th"}:
            self._chunks.append(" | ")
        if tag in {"h1", "h2", "p", "div", "section", "article", "tr", "footer"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self) -> str:
        compact_lines = []
        for line in "".join(f" {chunk} " if chunk != "\n" else chunk for chunk in self._chunks).splitlines():
            compact = re.sub(r"\s+", " ", line).strip()
            if compact:
                compact_lines.append(compact)
        return "\n".join(compact_lines)


def _html_text_content(html_doc: str) -> str:
    parser = _ReportTextExtractor()
    parser.feed(html_doc)
    return html.unescape(parser.text()).strip() or "AdsReport"
