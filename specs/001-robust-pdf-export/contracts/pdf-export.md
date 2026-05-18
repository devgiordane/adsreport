# Contract: Dashboard PDF Export

## User Interaction Contract

**Trigger**: User clicks the dashboard PDF export control.

**Inputs**:

- `filter-period.value`
- `filter-account.value`
- `filter-campaign.value`
- Active locale
- Authenticated dashboard session

**Successful Output**:

- Browser receives a downloadable file.
- `filename`: `adsreport-{account-or-all}-{date_from}-{date_to}.pdf`
- `content_type`: `application/pdf`
- PDF content includes branding, account context, selected period, generation timestamp, data freshness, KPI summary, trend section, breakdown section, campaign table, and footer.

**Unavailable Output**:

- No file is downloaded.
- User sees a localized message explaining that the selected period/account has no reportable data.
- Current filters remain unchanged.

**Failure Output**:

- No partial or corrupt file is downloaded.
- User sees a localized retryable error message.
- The failure is logged through the application's existing logging pattern.

## Callback Contract

**Callback responsibilities**:

- Normalize account/campaign filter inputs exactly as dashboard rendering does.
- Resolve date and comparison ranges from the selected period.
- Fetch report data through `ReportService`.
- Return unavailable state when no accounts or no data exist.
- Call the PDF export service with report data and report context.
- Return `dcc.Download` data for successful PDF bytes.

**Callback must not**:

- Invoke `window.print()`.
- Include sidebar, navbar controls, export buttons, debug menus, or filter widgets in the PDF.
- Persist generated files unless a later feature explicitly adds export history.

## PDF Rendering Contract

**Required sections, in order**:

1. Report header/cover area with AdsReport branding.
2. Context row with selected account(s), period, generated timestamp, and data freshness.
3. KPI summary.
4. Primary trend chart or chart summary.
5. Spend/campaign breakdown chart or chart summary.
6. Campaign performance table.
7. Ad set highlights table when available.
8. Footer with product/source context and page numbering where supported.

**Layout requirements**:

- A4 portrait by default.
- Multipage output must not clip cards, labels, or table rows.
- Long campaign names must wrap or truncate in a controlled way.
- Currency, percentages, and counts must use existing formatting conventions.
- Report labels must follow the active locale.

## Visual QA Contract

Before implementation is considered complete:

- Dashboard screenshot at desktop width shows refined layout without overlap.
- Dashboard screenshot at mobile-like width shows readable filter/export flow.
- Generated PDF with normal data opens successfully and contains required sections.
- Generated PDF with at least 100 campaign rows paginates without broken rows.
- No-data export shows message and does not download a blank PDF.
