# Data Model: Robust PDF Export and Visual Polish

## PDFReport

Represents one generated PDF document for a specific dashboard selection.

**Fields**:

- `title`: Human-readable report title.
- `generated_at`: Localized timestamp shown in the PDF.
- `account_labels`: Names or identifiers for the selected ad accounts.
- `date_from`: First included reporting date.
- `date_to`: Last included reporting date.
- `locale`: Label and formatting locale.
- `currency`: Currency used for money values, or a mixed-currency indicator.
- `data_freshness`: Most recent sync/data timestamp available for the selected accounts.
- `sections`: Ordered list of report sections.
- `filename`: Download filename containing account/date context.
- `content_type`: `application/pdf`.

**Validation Rules**:

- Must not be generated when there is no reportable data unless using an explicit no-data response.
- Must include account, period, generated timestamp, and branding.
- Filename must be filesystem-safe and descriptive.

## ReportSelection

Captures the dashboard state used to generate the report.

**Fields**:

- `account_ids`: Selected ad account IDs; defaults to dashboard default/active accounts.
- `campaign_ids`: Optional selected campaign IDs.
- `period`: Selected period token.
- `date_from`: Resolved start date.
- `date_to`: Resolved end date.
- `comparison_date_from`: Resolved prior-period start date.
- `comparison_date_to`: Resolved prior-period end date.
- `locale`: Active UI locale.

**Relationships**:

- A `ReportSelection` produces one `PDFReport`.
- A `ReportSelection` resolves to existing `ReportData` from `ReportService`.

**Validation Rules**:

- Date range must be valid and non-empty.
- Selected accounts must be visible to the authenticated user under existing dashboard rules.
- Campaign filters must be applied consistently to KPIs, charts, and tables.

## ReportSection

Represents a logical part of the PDF.

**Fields**:

- `kind`: One of `cover`, `summary`, `trend_chart`, `breakdown_chart`, `campaign_table`, `adset_table`, `footer`, `empty_state`.
- `title`: Localized section title.
- `content`: Prepared values, rows, or image references.
- `page_break_policy`: Whether the section should avoid internal page breaks, allow table pagination, or start on a new page.

**Validation Rules**:

- KPI and chart sections must use the same metric definitions as the dashboard.
- Table sections must allow pagination without splitting row content incoherently.
- Empty-state section must not be combined with normal metric sections.

## ExportState

Represents user-facing state during PDF generation.

**States**:

- `idle`: Export is available.
- `generating`: Request is in progress and duplicate export attempts are disabled.
- `success`: PDF bytes and filename are returned to the browser.
- `unavailable`: Current selection has no reportable data.
- `failed`: Generation failed and the user may retry.

**State Transitions**:

- `idle -> generating` when the user clicks export.
- `generating -> success` when PDF bytes are prepared.
- `generating -> unavailable` when current selection has no reportable data.
- `generating -> failed` when chart or PDF rendering raises an unrecoverable error.
- `success|unavailable|failed -> idle` after UI feedback is displayed or filters change.
