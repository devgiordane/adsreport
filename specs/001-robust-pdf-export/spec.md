# Feature Specification: Robust PDF Export and Visual Polish

**Feature Branch**: `001-robust-pdf-export`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "vamos melhorar o visual deixar muito mais robusta a exportação de PDF, não só um pdf de imprimir a tela"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Export a client-ready PDF report (Priority: P1)

As an AdsReport user, I want to export the selected dashboard data as a polished PDF report so I can share performance results with clients or stakeholders without manually reformatting screenshots.

**Why this priority**: This is the core value of the feature: the exported file must be a true report, not a browser printout, and must be useful outside the application.

**Independent Test**: Select an ad account and reporting period with available metrics, trigger PDF export, and verify that the downloaded file contains a branded cover/header, KPI summary, charts or chart summaries, campaign table, filters, date range, and footer information in a readable multipage layout.

**Acceptance Scenarios**:

1. **Given** a dashboard with synced campaign data and active filters, **When** the user exports a PDF report, **Then** the PDF includes the same selected account, date range, filters, KPIs, charts, and campaign details represented in a report-specific layout.
2. **Given** a report that spans more than one page, **When** the PDF is opened, **Then** content is paginated cleanly with no clipped cards, broken table rows, overlapping labels, or browser navigation artifacts.
3. **Given** a user shares the PDF outside AdsReport, **When** the recipient opens it, **Then** the document clearly identifies AdsReport, the report period, generation date, and the source ad account.

---

### User Story 2 - Improve the dashboard's visual quality (Priority: P2)

As an AdsReport user, I want the dashboard to look more refined and report-like so that the on-screen experience feels trustworthy and the exported PDF matches the product's visual standard.

**Why this priority**: A better PDF depends on consistent visual hierarchy, spacing, labels, and report components that feel credible both on screen and in export.

**Independent Test**: Open the dashboard on desktop and mobile-sized viewports and verify that KPI cards, charts, tables, filters, empty states, and export controls have consistent spacing, hierarchy, alignment, and responsive behavior.

**Acceptance Scenarios**:

1. **Given** a user views the dashboard, **When** they scan the page, **Then** key metrics, trends, filters, and export actions are visually grouped and easy to understand.
2. **Given** a dashboard with long campaign names or large numbers, **When** it renders on common screen sizes, **Then** text remains readable and does not overlap adjacent UI elements.
3. **Given** there is no synced data, **When** the dashboard loads, **Then** the page presents a polished empty state and prevents misleading PDF output.

---

### User Story 3 - Control export readiness and feedback (Priority: P3)

As an AdsReport user, I want clear feedback while a PDF is being prepared and useful error messages if it cannot be generated so I know whether the report is ready to share.

**Why this priority**: Robust export requires predictable user feedback, especially when data volume, missing data, or rendering delays affect generation.

**Independent Test**: Trigger exports for normal, empty, and unusually large report periods and verify that loading, disabled, success, and failure states are understandable and recoverable.

**Acceptance Scenarios**:

1. **Given** a user starts PDF export, **When** the report is being prepared, **Then** the export control communicates progress and prevents duplicate export attempts.
2. **Given** the selected period has no reportable data, **When** the user attempts export, **Then** the system explains what is missing and does not produce an empty or misleading PDF.
3. **Given** PDF generation fails, **When** the failure is shown, **Then** the user receives a clear message and can retry without losing the current filters.

---

### Edge Cases

- Very long campaign, ad set, or account names must wrap or truncate in a controlled way without overlapping adjacent content.
- Reports with many campaigns must paginate tables cleanly and repeat essential context when needed.
- Reports with missing optional metrics must indicate unavailable values without breaking layout.
- Exports must preserve the user's current account, date range, and filters at the moment export is requested.
- Export must not include private UI-only controls such as navigation, buttons, debug messages, or browser chrome.
- Users with stale or partially synced data must see the data freshness clearly in the PDF.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to generate a PDF report from the dashboard using the currently selected ad account, date range, and filters.
- **FR-002**: The PDF MUST use a report-specific layout rather than a direct printout of the visible screen.
- **FR-003**: The PDF MUST include a document title, AdsReport branding, generation date/time, selected period, selected account, and visible data freshness information.
- **FR-004**: The PDF MUST include the primary KPI summary with labels, values, period-over-period context where available, and clear formatting for currency, percentages, and counts.
- **FR-005**: The PDF MUST include campaign performance details in a readable table with clean pagination for long result sets.
- **FR-006**: The PDF MUST include chart content, chart summaries, or equivalent visual explanations for the dashboard's main trends and breakdowns.
- **FR-007**: The PDF MUST avoid clipped content, overlapping text, broken rows, browser navigation, interactive controls, and screen-only decoration.
- **FR-008**: The dashboard visual design MUST be refined for consistent spacing, typography hierarchy, card structure, filter controls, export controls, empty states, and responsive behavior.
- **FR-009**: The export flow MUST show clear loading, success, unavailable-data, and failure states.
- **FR-010**: The system MUST prevent duplicate export requests while a PDF is being generated.
- **FR-011**: The PDF file name MUST be descriptive enough to identify account and reporting period after download.
- **FR-012**: The export MUST respect the same access and data visibility rules as the dashboard.
- **FR-013**: The system MUST handle reports with no data, partial data, long labels, and large campaign tables without producing misleading or unreadable output.

### Key Entities *(include if feature involves data)*

- **PDF Report**: A generated document representing the selected dashboard state; includes title, branding, account, period, generated timestamp, data freshness, KPI summary, visual trend content, campaign table, and footer metadata.
- **Report Selection**: The user-selected account, date range, filters, locale, and metric context used to determine what appears in the report.
- **Report Section**: A logical part of the exported report such as header, KPI summary, trends, breakdowns, campaign table, empty-data notice, or footer.
- **Export State**: The user-facing status of PDF generation, including idle, generating, successful, unavailable because of missing data, and failed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can generate and download a client-ready PDF report for a normal dashboard period in under 10 seconds on a typical local deployment.
- **SC-002**: 100% of generated PDF pages in acceptance testing contain no clipped KPI cards, overlapping labels, browser navigation, or broken table rows.
- **SC-003**: The PDF includes all required report context fields in at least 95% of successful export test cases.
- **SC-004**: Reports with at least 100 campaign rows remain readable and correctly paginated.
- **SC-005**: At least 90% of test users can identify the account, report period, total spend, leads, and top campaign from the PDF without opening the dashboard.
- **SC-006**: Empty or unavailable-data exports produce a clear user message instead of a misleading blank report in 100% of tested no-data scenarios.

## Assumptions

- The first version exports the dashboard/report view for the currently authenticated user and does not add scheduled email delivery.
- The report should support both Portuguese and English labels using the application's existing language behavior.
- The PDF is intended for client or stakeholder sharing and should favor clarity over dense raw data dumps.
- Existing dashboard metrics and stored synced data remain the source of truth for report content.
- PNG export is outside this feature unless already supported by the existing dashboard.
