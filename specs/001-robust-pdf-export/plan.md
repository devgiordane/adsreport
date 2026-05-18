# Implementation Plan: Robust PDF Export and Visual Polish

**Branch**: `001-robust-pdf-export` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-robust-pdf-export/spec.md`

## Summary

Replace the current browser print-based dashboard export with a report-specific PDF generation flow. The implementation will keep the Dash dashboard as the interactive surface, add a server-side PDF export path backed by the existing report aggregation service, render Plotly charts as static assets, compose a branded multipage report template, and refresh dashboard styling so on-screen cards, charts, tables, filters, and empty states match the exported report quality.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Dash 2.x, Plotly, Flask-Login, SQLAlchemy, existing report repositories/services; planned additions are an HTML/CSS-to-PDF renderer and Plotly static image export support.

**Storage**: Existing SQLite database via SQLAlchemy; no new persistent tables required for v1 export.

**Testing**: pytest, pytest-playwright for rendered UI/export smoke checks, existing unit test style under `tests/unit`.

**Target Platform**: Self-hosted web app running locally or in Docker on Linux/Windows/macOS; browser-based Dash UI on desktop and responsive smaller viewports.

**Project Type**: Single Python web application with service layer, Dash UI, and repository-backed local data.

**Performance Goals**: Generate a normal PDF report in under 10 seconds; keep dashboard refresh responsive; preserve readable pagination for at least 100 campaign rows.

**Constraints**: Must not depend on printing the visible browser screen; must work in self-hosted and Docker deployments; must avoid leaking navigation, buttons, debug UI, or inactive filters into the PDF; must retain pt-BR/en-US labels.

**Scale/Scope**: Dashboard PDF export for the authenticated user's current report selection, covering KPI cards, primary trend chart, spend breakdown, campaign table, ad set highlights, empty/error states, and dashboard visual polish.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is still the placeholder template, so it defines no enforceable project-specific gates. Planning proceeds with the repository's observable standards instead: scoped changes, service-layer logic for report generation, i18n-aware UI text, and pytest coverage for service and callback behavior.

**Gate Status**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-robust-pdf-export/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- pdf-export.md
`-- tasks.md
```

### Source Code (repository root)

```text
adsreport/
|-- services/
|   |-- report_service.py
|   `-- pdf_export_service.py
|-- ui/
|   |-- callbacks/
|   |   `-- dashboard_callbacks.py
|   |-- components/
|   |   |-- chart_block.py
|   |   |-- data_table.py
|   |   `-- kpi_card.py
|   |-- pages/
|   |   `-- dashboard.py
|   `-- assets/
|       |-- adsreport.css
|       `-- report.css
|-- i18n/locales/
|   |-- en-US.json
|   `-- pt-BR.json
tests/
|-- unit/
|   |-- test_dashboard_callbacks.py
|   |-- test_dashboard_page.py
|   `-- test_pdf_export_service.py
`-- e2e/
    `-- test_dashboard_smoke.py
```

**Structure Decision**: Use the existing single-package Python web app structure. Keep data aggregation in `adsreport/services/report_service.py`, introduce PDF composition in a new service, expose it through the existing dashboard callback layer, and isolate PDF-specific styling in assets/templates rather than overloading print CSS.

## Complexity Tracking

No constitution violations identified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research

See [research.md](./research.md). Key decisions:

- Generate PDF server-side from report-specific HTML/CSS instead of `window.print()`.
- Export Plotly figures to static images before PDF composition.
- Use Dash `dcc.Download` for the user-facing download contract.

## Phase 1: Design

See [data-model.md](./data-model.md), [contracts/pdf-export.md](./contracts/pdf-export.md), and [quickstart.md](./quickstart.md).

## Constitution Check - Post Design

The design remains within the existing app structure, adds no persistent data store, preserves i18n requirements, and adds focused automated coverage. No new complexity exception is required.

**Gate Status**: PASS
