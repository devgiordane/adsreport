# Tasks: Robust PDF Export and Visual Polish

**Input**: Design documents from `/specs/001-robust-pdf-export/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/pdf-export.md, quickstart.md

**Tests**: Included because the specification defines measurable PDF/export and UI outcomes.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies and layout anchors required by the PDF export work.

- [x] T001 Add PDF/static chart dependencies to pyproject.toml
- [x] T002 Verify Python/Docker ignore patterns in .gitignore and .dockerignore
- [x] T003 Add dashboard PDF download component and export status container in adsreport/ui/pages/dashboard.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared report rendering structures and reusable chart builders required before user stories.

- [x] T004 [P] Add PDF export service unit tests in tests/unit/test_pdf_export_service.py
- [x] T005 [P] Add dashboard export callback tests in tests/unit/test_dashboard_callbacks.py
- [x] T006 Add shared dashboard figure builder helpers in adsreport/ui/callbacks/dashboard_callbacks.py
- [x] T007 Create PDF export service skeleton and value objects in adsreport/services/pdf_export_service.py

---

## Phase 3: User Story 1 - Export a client-ready PDF report (Priority: P1) MVP

**Goal**: Generate a branded, report-specific PDF download from the selected dashboard data.

**Independent Test**: Trigger export for a dashboard selection with data and verify the downloaded PDF bytes include report context and no print-screen artifacts.

- [x] T008 [US1] Implement PDF report HTML/CSS rendering in adsreport/services/pdf_export_service.py
- [x] T009 [US1] Implement Plotly static chart image export with text fallback in adsreport/services/pdf_export_service.py
- [x] T010 [US1] Implement dashboard PDF download callback in adsreport/ui/callbacks/dashboard_callbacks.py
- [x] T011 [US1] Add PDF export i18n labels in adsreport/i18n/locales/en-US.json and adsreport/i18n/locales/pt-BR.json
- [x] T012 [US1] Run and fix US1 unit tests for tests/unit/test_pdf_export_service.py and tests/unit/test_dashboard_callbacks.py

---

## Phase 4: User Story 2 - Improve the dashboard's visual quality (Priority: P2)

**Goal**: Make the dashboard more polished and aligned with the new report experience.

**Independent Test**: Open desktop and small viewport dashboard layouts and verify KPI cards, charts, filters, tables, and export actions do not overlap and have consistent hierarchy.

- [x] T013 [US2] Refine dashboard structure and export action grouping in adsreport/ui/pages/dashboard.py
- [x] T014 [US2] Improve dashboard/card/chart/table responsive styling in adsreport/ui/assets/adsreport.css
- [x] T015 [US2] Update dashboard page tests in tests/unit/test_dashboard_page.py
- [x] T016 [US2] Run and fix dashboard page/unit tests

---

## Phase 5: User Story 3 - Control export readiness and feedback (Priority: P3)

**Goal**: Provide loading, success, no-data, and retryable failure states without duplicate export attempts.

**Independent Test**: Trigger normal, no-data, and failing export paths and verify user feedback while filters remain unchanged.

- [x] T017 [US3] Add export status outputs and no-data/failure handling in adsreport/ui/callbacks/dashboard_callbacks.py
- [x] T018 [US3] Add localized status messages in adsreport/i18n/locales/en-US.json and adsreport/i18n/locales/pt-BR.json
- [x] T019 [US3] Extend dashboard callback tests for unavailable and failed export states in tests/unit/test_dashboard_callbacks.py
- [x] T020 [US3] Run and fix export feedback tests

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation consistency.

- [x] T021 Run lint/type/test checks for touched modules
- [x] T022 Update quickstart notes if implementation behavior differs in specs/001-robust-pdf-export/quickstart.md
- [x] T023 Validate task completion and mark all finished tasks in specs/001-robust-pdf-export/tasks.md

---

## Dependencies & Execution Order

- Phase 1 must complete before Phase 2.
- Phase 2 must complete before any user story implementation.
- User Story 1 is the MVP and should complete before User Stories 2 and 3.
- User Story 2 and User Story 3 can be worked independently after User Story 1, but this implementation executes them sequentially to avoid touching the same UI/callback files concurrently.
- Phase 6 depends on all selected user stories.

## Parallel Opportunities

- T004 and T005 can be written in parallel because they target different test surfaces.
- Styling changes in T014 can be reviewed independently from callback feedback logic after T010 is complete.

## Implementation Strategy

1. Establish dependencies and Dash download placeholders.
2. Add tests for PDF service and callback behavior.
3. Implement the PDF service and callback until User Story 1 passes.
4. Refine visual styling for User Story 2.
5. Add no-data/failure feedback for User Story 3.
6. Run targeted validation and update this task list.
