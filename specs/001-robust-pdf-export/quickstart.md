# Quickstart: Robust PDF Export and Visual Polish

## Prerequisites

- Python 3.11+
- Project dependencies installed through the existing project workflow
- Local database with at least one synced ad account and campaign insights

## Run the App

```powershell
hatch run dev
```

Open `http://localhost:8050`.

## Manual Validation

1. Sign in and open the dashboard.
2. Select an account, period, and optionally campaigns.
3. Confirm the dashboard visual layout is polished on desktop width:
   - KPI cards align cleanly.
   - Charts and tables have clear hierarchy.
   - Export action is visible but not visually dominant.
   - Long labels do not overlap.
4. Click the PDF export control.
5. Confirm the browser downloads a PDF with a descriptive filename.
6. Open the PDF and verify:
   - It is not a direct screenshot or browser printout.
   - It contains AdsReport branding, account, period, generation time, and data freshness.
   - KPI summary, charts or chart summaries, campaign table, and footer are present.
   - Multipage content is readable with no clipped rows or overlapping text.
7. Select a period/account with no data and confirm export shows a clear message instead of downloading a blank report.

## Automated Checks

```powershell
hatch run test tests/unit/test_pdf_export_service.py
hatch run test tests/unit/test_dashboard_callbacks.py
hatch run test tests/unit/test_dashboard_page.py
hatch run test tests/e2e/test_dashboard_smoke.py
```

## Regression Checklist

- Existing dashboard data still loads from `ReportService`.
- Existing campaign/ad set tables still honor ROAS availability.
- Current locale remains reflected in dashboard and PDF labels.
- Export button cannot trigger duplicate generation while a request is active.
- Failed generation logs an error and leaves filters unchanged.
