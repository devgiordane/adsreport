# Research: Robust PDF Export and Visual Polish

## Decision: Generate PDFs from server-side report HTML/CSS

**Decision**: Replace the current `window.print()` export with a backend report renderer that builds purpose-made HTML/CSS and converts it to PDF.

**Rationale**: The current flow prints the dashboard surface, so it inherits browser chrome risks, responsive layout compromises, and print CSS fragility. A report renderer gives control over headers, footers, pagination, table flow, branding, and document-only metadata. WeasyPrint's documentation describes HTML/CSS-to-PDF rendering with pagination, margins, headers, and footers, while also noting that it does not execute JavaScript, which fits a pre-rendered report template.

**Alternatives considered**:

- Browser print: already implemented but fails the feature's "not just print the screen" requirement.
- Headless browser PDF: strong visual parity with the app, but heavier operationally and more coupled to Dash's interactive DOM.
- Low-level PDF drawing: maximum control but slower to build and harder to keep visually aligned with dashboard design.

**References**:

- WeasyPrint overview and limitations: https://weasyprint.com/

## Decision: Convert Plotly figures to static images for PDF sections

**Decision**: Reuse the same figure-building logic conceptually, but export charts to static images before embedding them in the PDF report.

**Rationale**: PDF renderers need static assets, not interactive Dash graphs. Plotly's official static image export documentation supports exporting figures to image bytes and files using Kaleido, including PNG, SVG, and PDF formats. Static chart generation also lets tests assert that report sections are present without depending on the live browser DOM.

**Alternatives considered**:

- Embed interactive charts directly: not suitable for a PDF document.
- Rebuild charts manually in SVG/HTML: increases duplication and risks metric mismatches.
- Use chart summaries only: acceptable fallback for failures, but not enough for the primary report experience.

**References**:

- Plotly static image export: https://plotly.com/python/static-image-export/
- Dash static image export notes: https://dash.plotly.com/jupyter-notebooks/static-images

## Decision: Use Dash download state instead of opening a print dialog

**Decision**: Add a `dcc.Download` component and a callback that returns PDF bytes with a descriptive filename.

**Rationale**: Dash's `dcc.Download` component opens a download dialog when its `data` property changes, which matches the desired user flow better than invoking browser print. It also gives callbacks a clean place to return unavailable-data and failure states while preserving filters.

**Alternatives considered**:

- Keep clientside callback: too limited for robust error states and server-generated files.
- Add a separate public download URL: unnecessary for v1 and would broaden auth/security scope.

**References**:

- Dash `dcc.Download`: https://dash.plotly.com/dash-core-components/download

## Decision: Keep report generation ephemeral

**Decision**: Generate PDF bytes on demand without storing report files or export history in the database.

**Rationale**: The specification only requires current-dashboard export. Persisting generated files would add retention, cleanup, privacy, and storage concerns that are not necessary for the first version.

**Alternatives considered**:

- Persist every report: useful for audit/history, but not requested and higher privacy burden.
- Cache generated files by filter selection: could improve repeated exports, but risks stale data and adds invalidation complexity.

## Decision: Treat visual polish as shared component refinement plus PDF-specific styling

**Decision**: Improve dashboard spacing, hierarchy, states, and table/chart readability in existing Dash components/CSS, while keeping PDF-only page layout in dedicated report styles/templates.

**Rationale**: The dashboard should feel more refined, but PDF requirements such as A4 pagination, repeated footers, and page-break behavior should not be forced into the interactive layout.

**Alternatives considered**:

- PDF-only redesign: would leave the dashboard feeling inconsistent.
- One CSS layout for both screen and PDF: simpler initially, but the existing print CSS already shows the fragility of that approach.
