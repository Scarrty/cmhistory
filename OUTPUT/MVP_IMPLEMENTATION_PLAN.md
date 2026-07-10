# MVP Implementation Plan

## Goal

Build a small, local-first Cardmarket Sales/Purchase Dashboard from the existing export files in `D:\OneDrive\Dokumente\CM History`.

The MVP must reliably import current and future monthly Cardmarket XLS/CSV exports, normalize article and shipment data into linked records, validate known source-data edge cases, and provide a practical browser dashboard for filtering, drilling into orders/articles, and creating simple period reports.

This plan does not implement the product. It defines the implementation path and the verification gates.

## MVP Definition

The smallest practical MVP is:

| Capability | MVP Decision | Reason |
|---|---:|---|
| Local file import for XLS and CSV exports | Keep | This is the source of truth and the core workflow. |
| Filename-based classification | Keep | The exports encode direction, report type, date basis, and month in filenames. |
| Raw staging of every imported row | Keep | Required to debug grouped shipment rows, duplicate files, parser issues, and future export changes. |
| Shipment grouped-row normalization | Keep | Shipment files are not clean one-row-per-order tables; continuation rows must inherit the previous order. |
| Article-to-shipment linking by order ID | Keep | The product goal requires related records to be genuinely connected. |
| Product, expansion, category, and localized labels | Keep | Needed for article/product filters and robust handling of localized names. |
| Basic date, article, product, expansion, category, direction, username, country, and order filters | Keep | These are the main analysis axes in the PRD and source model. |
| Minimal period reports | Keep | A usable dashboard needs date-range totals and exportable summaries. |
| Basic charts | Keep, limited | Use simple monthly totals/counts first; avoid a charting-heavy product before data quality is proven. |
| Import validation report | Keep | The feasibility review found concrete edge cases that must be visible. |
| Public hosting, multi-user login, complex roles | Defer | Current data contains personal/business data and is safest as local-only MVP. |
| Tax-grade accounting, FIFO profit, inventory valuation | Defer | Not supported enough by the current PRD/source model for MVP. |
| PDF report generation and saved dashboard layouts | Defer | Nice-to-have, not required to prove the core import and analysis model. |

## Non-Goals

- No implementation work in this planning step.
- No React/Vue/Angular single-page app for MVP unless later justified by real UI complexity.
- No public deployment or cloud storage in MVP.
- No Cardmarket API integration.
- No automatic email/Drive import.
- No PDF export.
- No tax, VAT, FIFO, margin, or inventory accounting claims.
- No saved filter sets or scheduled reports.
- No editable source data in the dashboard.
- No destructive cleanup of source XLS/CSV files.
- No copying personal address data into test fixtures unless explicitly approved.

## Source Alignment

| Source | Path | Relevant Evidence Used |
|---|---|---|
| Feasibility review | `D:\OneDrive\Dokumente\CM History\OUTPUT\PRD_FEASIBILITY_REVIEW.md` | Verdict `READY WITH CHANGES`; source inventory; grouped shipment rows; parser/Unicode risk; duplicate CSV/XLS overlap; recommended MVP scope and architecture. |
| PRD | `D:\OneDrive\Dokumente\CM History\PRD_Cardmarket_Dashboard.md` | Product goal: import Excel files, link related data, filter by date/article/properties, create period reports, show charts, support future monthly imports. |
| Data model | `D:\OneDrive\Dokumente\CM History\Datenmodell.md` | Derived entities: import files, articles, shipments, shipment events, products, expansions, categories, users, money fields, date-basis handling. |
| XLS/CSV source exports | `D:\OneDrive\Dokumente\CM History\*.XLS`, `D:\OneDrive\Dokumente\CM History\*.CSV` | Canonical business data: 447 total files, 21,172 nonblank rows, one `Worksheet` sheet per XLS, 2016-04-01 through 2026-07-06. |

Key source constraints from the feasibility review:

- Shipment exports contain grouped rows. Out of 10,596 shipment raw rows, 8,432 rows have blank `OrderID`/`Username` and must inherit the current shipment header row.
- Purchase-date and payment-date exports are separate views of the same business activity and have incomplete monthly coverage in several periods.
- 2026 sold article CSV/XLS pairs overlap exactly after normalization and must not be double-counted.
- At least one XLS needs tolerant parsing: `PURCHASED ARTICLES-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS`.
- Unicode fidelity must be verified because one parser path replaced non-ASCII characters in a private address value.
- Product IDs are stable, but localized product names are not one-to-one. The data contains 4,065 product IDs and 63 product IDs with multiple localized names.

## Assumptions

| Assumption | Impact | Validation Point |
|---|---|---|
| The MVP can be local-only on the user's machine. | Allows SQLite and avoids user/auth/security scope. | Human approval before implementation. |
| Python is acceptable for import and web app. | Simplest fit for spreadsheet parsing, validation, and local dashboard. | Human approval before implementation. |
| SQLite is enough for the current dataset and future monthly imports. | Keeps setup small; can migrate later if hosted/multi-user. | Import all current files and run dashboard queries under acceptable latency. |
| The source folder remains the canonical import location. | Avoids a separate upload workflow in the first version. | Human approval before implementation. |
| Future files follow the current filename families. | Enables deterministic classification. | Validate unknown filenames and surface them as import issues. |
| Personal address/name data should be masked in default UI views. | Reduces privacy risk. | Human approval for any unmasked detail view. |
| Charts can start with basic monthly totals and counts. | Avoids overbuilding visualization before data trust is established. | Confirm after first imported database review. |

## Architecture Overview

Recommended MVP stack:

| Layer | Recommendation | Rationale |
|---|---|---|
| Runtime | Python 3.12+ | Strong spreadsheet/data tooling and simple local deployment. |
| Web framework | FastAPI with server-rendered Jinja templates | Small, testable, enough for filters/tables/charts without SPA complexity. |
| Database | SQLite | Local-first, portable, sufficient for 21k current rows plus monthly growth. |
| Import tooling | CLI module plus reusable importer service | Enables repeatable verification before UI work. |
| Charting | Lightweight browser chart library from static assets | Basic line/bar charts only. |
| Tests | pytest | Straightforward unit/integration coverage for parsing and import rules. |
| Formatting/lint | ruff | Fast local quality check. |

Simplest viable data flow:

1. Scan `D:\OneDrive\Dokumente\CM History` for `.XLS`, `.XLSX`, and `.CSV`.
2. Parse each filename into `direction`, `entity`, `date_basis`, `period_start`, `period_end`, and extension.
3. Record each file in `import_files` with path, hash, parsed metadata, import status, and parser warnings.
4. Read each workbook/sheet into raw staging rows exactly as seen, including source row number and source columns.
5. For shipment exports, compute `resolved_order_id` by forward-filling from the latest nonblank shipment header row.
6. Normalize dates, decimals, text, booleans, currencies, quantities, and source-specific empty values.
7. Upsert normalized shipments, shipment events, article lines, products, product labels, categories, and expansions.
8. Deduplicate exact overlapping CSV/XLS article exports by normalized business keys and source priority.
9. Run validation checks and store issues in `import_issues`.
10. Serve dashboard views from normalized read queries, always linking back to source file/row details.

Suggested folder layout:

```text
D:\OneDrive\Dokumente\CM History\
  pyproject.toml
  README.md
  .gitignore
  data\
    .gitkeep
  migrations\
    001_init.sql
  src\
    cm_dashboard\
      __init__.py
      cli.py
      config.py
      db.py
      importing\
        __init__.py
        filename.py
        readers.py
        normalize.py
        pipeline.py
        validation.py
      reporting\
        __init__.py
        queries.py
      web\
        __init__.py
        app.py
        templates\
          base.html
          dashboard.html
          imports.html
          shipments.html
          shipment_detail.html
          articles.html
          product_detail.html
        static\
          app.css
          app.js
  tests\
    test_filename_parser.py
    test_readers.py
    test_normalize.py
    test_shipment_grouping.py
    test_deduplication.py
    test_schema.py
    test_import_pipeline.py
    test_reporting_queries.py
```

## Data Model Mapping

| Source Field / Concept | MVP Table / Field | Notes |
|---|---|---|
| Source filename | `import_files.original_path`, `direction`, `entity`, `date_basis`, `period_start`, `period_end` | Filename parsing is required before row parsing. |
| Source file hash | `import_files.file_hash` | Required for idempotent import and duplicate detection. |
| Sheet name `Worksheet` | `import_files.sheet_name` | Store for diagnostics even though all XLS observed use the same name. |
| Source row number | `raw_article_rows.source_row_number`, `raw_shipment_rows.source_row_number` | Required for traceability and debugging. |
| `Shipment nr.` / `OrderID` | `shipments.order_id`, `raw_*_rows.order_id` | Primary business link across articles and shipments. |
| Blank shipment continuation row order ID | `raw_shipment_rows.resolved_order_id` | Forward-filled from previous shipment header row. |
| Purchase/payment report type | `shipment_events.event_type`, `shipment_events.event_date` | Store purchase and payment dates as distinct event facts. |
| `Date of purchase`, `Date of payment` | `shipment_events.event_date` | Date basis must not be collapsed into one ambiguous date. |
| `Username` | `shipments.username` | Keep as order snapshot; optional future user dimension. |
| Buyer/seller name/address fields | `shipments.counterparty_*` | Store only if present; mask by default in UI. |
| `Country` | `shipments.country` | Filterable dimension. |
| `is professional`, `VAT-ID` | `shipments.is_professional`, `shipments.vat_id_present` | Avoid exposing full VAT ID by default. |
| `Product ID` | `products.product_id`, `article_lines.product_id` | Product ID is stable, but names can vary. |
| `Product Name`, `Localized Product Name`, `Article` | `product_labels`, `article_lines.article_name_snapshot` | Preserve observed labels by source row. |
| `Expansion` | `expansions.name`, `article_lines.expansion_name_snapshot` | Normalize lightly; preserve snapshot text. |
| `Category` | `categories.name`, `article_lines.category_name_snapshot` | Normalize lightly; preserve snapshot text. |
| `Amount` | `article_lines.quantity` | Integer quantity. |
| `Article Value`, `Total` | `article_lines.unit_value`, `article_lines.line_total` | Decimal money values, never floats. |
| `Currency` | `article_lines.currency`, `shipments.currency` | Store explicitly where source provides it. |
| `Article Count`, `Merchandise Value`, `Shipment Costs`, `Trustee service fee`, `Commission`, `Total Value` | `shipment_financials` or columns on `shipments` | Keep shipment-level financial totals separate from line totals. |
| `Comments`, `Description` | `article_lines.comment`, `shipments.description` | Text search later; plain storage in MVP. |
| Import errors/warnings | `import_issues` | Required for reviewable importer output. |

Minimum normalized tables:

- `import_files`
- `raw_article_rows`
- `raw_shipment_rows`
- `shipments`
- `shipment_events`
- `article_lines`
- `products`
- `product_labels`
- `expansions`
- `categories`
- `import_issues`

Optional only if needed during implementation:

- `shipment_financials`, if shipment totals are too wide for `shipments`.
- `counterparties`, if username/name/address normalization becomes useful after MVP validation.

## MVP Acceptance Criteria

| Requirement | Acceptance Criterion |
|---|---|
| Source scanning | A command scans the folder and reports 447 known source files plus any unknown files without crashing. |
| Filename parsing | All current XLS/CSV filenames are classified into direction, entity, date basis, and period; malformed filenames are reported as issues. |
| XLS parsing | The importer reads the known tolerant-parser fixture `PURCHASED ARTICLES-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS`. |
| Unicode fidelity | Non-ASCII address text is preserved without replacement characters in `PURCHASED SHIPMENTS-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS`. |
| CSV parsing | 2026 sold article CSV files import with the same row shape as their XLS counterparts. |
| Raw staging | Every imported source row is stored with file ID, source row number, raw values, and parser metadata. |
| Shipment grouping | Continuation rows in shipment exports receive the correct `resolved_order_id`; known continuation counts match the feasibility review. |
| Article/shipment linking | Linked views can show article rows under their shipment/order using `order_id`. |
| Duplicate handling | Exact overlapping 2026 sold article CSV/XLS pairs do not double-count in normalized reports. |
| Date-basis handling | Purchase-date and payment-date exports remain distinguishable in import metadata and report filters. |
| Missing coverage visibility | Missing/asymmetric monthly exports are shown in import validation output. |
| Product names | Product IDs can have multiple observed localized names without overwriting history. |
| Dashboard filters | UI filters by date range, direction, date basis, order ID, product ID/name, expansion, category, username, and country. |
| Period report | A date range report shows totals for purchases/sales, shipment counts, article-line counts, and merchandise/shipping/fee totals where available. |
| Basic charts | Dashboard shows at least one monthly sales/purchase total chart and one article-count or shipment-count chart. |
| Privacy default | Address/name/VAT details are hidden or masked in list views by default. |
| Repeat import | Re-running import on the same source folder is idempotent and does not duplicate normalized facts. |
| Future monthly import | Adding a new correctly named monthly file imports it without schema changes. |

## Verifier Commands

These commands define the expected verification interface to build. They are not available until the implementation tasks create the project.

```powershell
cd "D:\OneDrive\Dokumente\CM History"
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check src tests
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source --source "D:\OneDrive\Dokumente\CM History"
.\.venv\Scripts\python -m cm_dashboard.cli import --source "D:\OneDrive\Dokumente\CM History" --db "data\cardmarket.db"
.\.venv\Scripts\python -m cm_dashboard.cli validate --db "data\cardmarket.db"
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app --reload
```

Expected final verification:

- `pytest` passes.
- `ruff check src tests` passes.
- `inspect-source` reports the expected current source inventory and unknown-file issues only for intentionally unsupported files.
- `import` completes without unhandled exceptions.
- `validate` reports known coverage gaps and zero critical parser/linking failures.
- The web app opens locally and shows dashboard/import/explorer pages.

Because this folder is currently not a Git repository, `git diff --check` is not applicable until a repository is initialized.

## Implementation Tasks

Each task is intentionally small and should be committed separately once the folder is under Git. The commit commands are included for implementation-time use.

### Task 1: Create Project Skeleton

**Objective:** Add the minimal Python project structure without import logic.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\pyproject.toml`
- Create `D:\OneDrive\Dokumente\CM History\.gitignore`
- Create `D:\OneDrive\Dokumente\CM History\README.md`
- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\__init__.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\__init__.py`

**Steps:**

1. Define package metadata, Python version, runtime dependencies, and dev dependencies.
2. Add `.venv`, `data\*.db`, caches, and temporary files to `.gitignore`.
3. Add a short README with local-first scope and no implementation claims beyond setup.
4. Run:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Expected: package installs.

5. Commit:

```powershell
git add pyproject.toml .gitignore README.md src tests
git commit -m "Create dashboard project skeleton"
```

**Acceptance:** Editable install works and no source XLS/CSV files are modified.

### Task 2: Add Configuration Module

**Objective:** Centralize source path and database path handling.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\config.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_config.py`

**Steps:**

1. Add tests for default source path, explicit source path, default database path, and path normalization.
2. Implement a small settings object.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_config.py
```

Expected: tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\config.py tests\test_config.py
git commit -m "Add local configuration handling"
```

**Acceptance:** Commands can later receive source and database paths consistently.

### Task 3: Add Fixture Manifest Without Copying Personal Data

**Objective:** Document which real source files are used for regression tests.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\tests\fixtures_manifest.md`
- Create `D:\OneDrive\Dokumente\CM History\tests\fixtures.py`

**Steps:**

1. List fixture paths for tolerant XLS parsing, Unicode fidelity, grouped shipment rows, CSV/XLS duplication, and missing coverage.
2. Add helper functions that locate fixture files in the workspace without copying them.
3. Add a test that skips with a clear message if a fixture file is missing.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests
```

Expected: existing tests pass.

5. Commit:

```powershell
git add tests\fixtures_manifest.md tests\fixtures.py
git commit -m "Document source fixtures for importer tests"
```

**Acceptance:** Tests can reference canonical source files while keeping private data out of copied fixtures.

### Task 4: Implement Filename Parser

**Objective:** Parse Cardmarket export filenames into structured metadata.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\__init__.py`
- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\filename.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_filename_parser.py`

**Steps:**

1. Add tests for purchased/sold, articles/shipments, by-purchase-date/by-payment-date, XLS, CSV, period start, and period end.
2. Add tests for invalid filenames returning structured errors.
3. Implement parser with explicit enums or constants.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_filename_parser.py
```

Expected: parser tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing tests\test_filename_parser.py
git commit -m "Parse Cardmarket export filenames"
```

**Acceptance:** All current filename families can be represented without guessing row contents.

### Task 5: Implement Source Scanner

**Objective:** Find importable source files and classify them using the filename parser.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\source_scan.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_source_scan.py`

**Steps:**

1. Add tests for scanning `.XLS`, `.XLSX`, `.CSV`, and ignoring documentation/output files.
2. Add an integration-style test against the current folder that expects the known source count from the feasibility review.
3. Implement deterministic sorted scanning.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_source_scan.py
```

Expected: scanner tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing\source_scan.py tests\test_source_scan.py
git commit -m "Scan Cardmarket source exports"
```

**Acceptance:** The scanner reports current importable files and unknown candidates clearly.

### Task 6: Choose and Wrap Spreadsheet Readers

**Objective:** Add a reader interface for XLS and CSV without normalization logic.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\readers.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_readers.py`

**Steps:**

1. Add tests that read sheet name, header row, row count, and sample cells from an XLS.
2. Add tests that read a CSV with the same interface.
3. Include the known tolerant parser fixture `PURCHASED ARTICLES-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS`.
4. Implement the smallest reader abstraction that preserves raw cell values.
5. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_readers.py
```

Expected: reader tests pass.

6. Commit:

```powershell
git add src\cm_dashboard\importing\readers.py tests\test_readers.py
git commit -m "Add spreadsheet reader abstraction"
```

**Acceptance:** XLS and CSV files can be read through one interface and parser errors are explicit.

### Task 7: Add Unicode Fidelity Regression

**Objective:** Prevent silent character corruption in source parsing.

**Files:**

- Modify `D:\OneDrive\Dokumente\CM History\tests\test_readers.py`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\readers.py`

**Steps:**

1. Add a test proving that non-ASCII address text is preserved without publishing the private value.
2. If the current XLS library fails, adjust the reader or parser dependency until the test passes.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_readers.py
```

Expected: Unicode fidelity test passes.

4. Commit:

```powershell
git add pyproject.toml src\cm_dashboard\importing\readers.py tests\test_readers.py
git commit -m "Preserve Unicode text when reading exports"
```

**Acceptance:** The importer never proceeds with known mojibake in this fixture.

### Task 8: Define Source Header Schemas

**Objective:** Capture expected columns for each export family.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\schemas.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_source_schemas.py`

**Steps:**

1. Add tests for article and shipment column detection.
2. Add tests for unknown/missing/extra columns producing warnings, not crashes.
3. Implement schema definitions based on current source headers.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_source_schemas.py
```

Expected: schema tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing\schemas.py tests\test_source_schemas.py
git commit -m "Define Cardmarket export source schemas"
```

**Acceptance:** Header validation is explicit and future export changes are reportable.

### Task 9: Implement Normalizers

**Objective:** Convert raw dates, decimals, integers, booleans, and empty values consistently.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\normalize.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_normalize.py`

**Steps:**

1. Add tests for European decimal values, empty cells, dates, quantities, boolean-like fields, currency, and trimmed text.
2. Implement decimal handling with `Decimal`, not `float`.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_normalize.py
```

Expected: normalizer tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\importing\normalize.py tests\test_normalize.py
git commit -m "Normalize export cell values"
```

**Acceptance:** Money values are stored exactly enough for reporting and not as binary floats.

### Task 10: Implement Shipment Grouping

**Objective:** Resolve continuation rows in shipment exports.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\shipment_grouping.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_shipment_grouping.py`

**Steps:**

1. Add tests for header rows and blank continuation rows using source rows from the grouped shipment fixture.
2. Assert the known grouped-row counts from the feasibility review for each shipment family.
3. Implement forward-fill of `resolved_order_id` and inherited shipment header fields.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_shipment_grouping.py
```

Expected: grouping tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing\shipment_grouping.py tests\test_shipment_grouping.py
git commit -m "Resolve grouped shipment export rows"
```

**Acceptance:** Continuation rows link to the correct order and counts match the inspected XLS evidence.

### Task 11: Implement Duplicate Business Keys

**Objective:** Detect exact duplicate records across overlapping CSV/XLS exports.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\deduplication.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_deduplication.py`

**Steps:**

1. Add tests for the January 2026 sold articles CSV/XLS pair.
2. Define normalized article-line business key from order ID, product/article identifiers, quantity, value, date basis, and row content.
3. Implement duplicate-key generation only; do not yet delete data.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_deduplication.py
```

Expected: CSV/XLS duplicates produce matching keys.

5. Commit:

```powershell
git add src\cm_dashboard\importing\deduplication.py tests\test_deduplication.py
git commit -m "Detect duplicate export rows by business key"
```

**Acceptance:** Known overlapping CSV/XLS rows can be identified before aggregation.

### Task 12: Create SQLite Schema Migration

**Objective:** Add the initial database schema.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\migrations\001_init.sql`
- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\db.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_schema.py`

**Steps:**

1. Add tests that create a temporary database and verify all required tables and indexes exist.
2. Write migration for import files, raw rows, normalized entities, and import issues.
3. Add a migration runner.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_schema.py
```

Expected: schema tests pass.

5. Commit:

```powershell
git add migrations\001_init.sql src\cm_dashboard\db.py tests\test_schema.py
git commit -m "Create initial SQLite schema"
```

**Acceptance:** A fresh database can be created from migrations only.

### Task 13: Store Import Files and Raw Rows

**Objective:** Persist file metadata and exact raw source rows.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\raw_store.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_raw_store.py`

**Steps:**

1. Add tests for storing an import file with parsed metadata and hash.
2. Add tests for storing raw article and raw shipment rows with source row numbers.
3. Implement inserts with transaction boundaries.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_raw_store.py
```

Expected: raw storage tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing\raw_store.py tests\test_raw_store.py
git commit -m "Persist import files and raw source rows"
```

**Acceptance:** Source traceability exists before normalization.

### Task 14: Normalize Products and Article Lines

**Objective:** Convert raw article exports into product labels and article lines.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\article_import.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_article_import.py`

**Steps:**

1. Add tests for product ID, localized names, expansion, category, quantity, values, and comments.
2. Add a test proving one product ID can keep multiple observed localized labels.
3. Implement article normalization into normalized tables.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_article_import.py
```

Expected: article import tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing\article_import.py tests\test_article_import.py
git commit -m "Normalize article exports into product lines"
```

**Acceptance:** Article facts can be reported without losing source label history.

### Task 15: Normalize Shipments and Events

**Objective:** Convert raw shipment exports into shipments, event dates, and shipment financials.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\shipment_import.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_shipment_import.py`

**Steps:**

1. Add tests for order ID, username, country, purchase/payment event date, shipment totals, fees, and grouped continuation rows.
2. Implement shipment normalization using `resolved_order_id`.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_shipment_import.py
```

Expected: shipment import tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\importing\shipment_import.py tests\test_shipment_import.py
git commit -m "Normalize shipment exports into linked orders"
```

**Acceptance:** Shipment records and event dates are queryable by order and date basis.

### Task 16: Link Article Lines to Shipments

**Objective:** Ensure normalized article lines connect to normalized shipment/order records.

**Files:**

- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\article_import.py`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\shipment_import.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_article_shipment_linking.py`

**Steps:**

1. Add tests for known source families with zero unmatched order IDs where the feasibility review found full matches.
2. Add tests that unmatched order IDs become validation issues, not silent failures.
3. Implement linking by order ID.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_article_shipment_linking.py
```

Expected: linking tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing tests\test_article_shipment_linking.py
git commit -m "Link article lines to shipment orders"
```

**Acceptance:** Dashboard drill-down can show which articles belong to which order.

### Task 17: Build Import Pipeline

**Objective:** Combine scanning, parsing, raw staging, normalization, and validation entry points.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\pipeline.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_import_pipeline.py`

**Steps:**

1. Add tests for importing a small selected set of real fixture files into a temporary database.
2. Add tests for transaction rollback on parser failure.
3. Implement pipeline orchestration.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_import_pipeline.py
```

Expected: pipeline tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\importing\pipeline.py tests\test_import_pipeline.py
git commit -m "Add end-to-end import pipeline"
```

**Acceptance:** A representative import can run through the full path in one call.

### Task 18: Make Imports Idempotent

**Objective:** Re-importing the same files must not duplicate facts.

**Files:**

- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\pipeline.py`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\raw_store.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_idempotent_import.py`

**Steps:**

1. Add tests that run the same import twice and compare normalized counts.
2. Use file hash and business keys to skip or replace safely.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_idempotent_import.py
```

Expected: second import does not change normalized fact counts.

4. Commit:

```powershell
git add src\cm_dashboard\importing tests\test_idempotent_import.py
git commit -m "Make source imports idempotent"
```

**Acceptance:** Monthly refreshes are safe to rerun.

### Task 19: Add Import Validation Checks

**Objective:** Store reviewable warnings/errors for source quality and import consistency.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\importing\validation.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_import_validation.py`

**Steps:**

1. Add checks for grouped shipment counts, missing monthly coverage, unmatched orders, duplicate source rows, unknown columns, and parser warnings.
2. Assert known missing coverage examples from the feasibility review are reported.
3. Implement validation issue storage.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_import_validation.py
```

Expected: validation tests pass and known issues are explicit.

5. Commit:

```powershell
git add src\cm_dashboard\importing\validation.py tests\test_import_validation.py
git commit -m "Validate imported Cardmarket source data"
```

**Acceptance:** Known source-data caveats are visible instead of hidden in reports.

### Task 20: Add CLI Entry Point

**Objective:** Provide repeatable commands for source inspection, import, and validation.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\cli.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_cli.py`

**Steps:**

1. Add tests for `inspect-source`, `import`, and `validate` command argument parsing.
2. Wire CLI commands to scanner, pipeline, and validation services.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_cli.py
```

Expected: CLI tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\cli.py tests\test_cli.py
git commit -m "Add import and validation CLI"
```

**Acceptance:** The verifier commands have real entry points.

### Task 21: Import the Full Current Source Folder

**Objective:** Prove the importer works against all current source files.

**Files:**

- Modify importer files only if full import exposes a defect.
- Create or update `D:\OneDrive\Dokumente\CM History\tests\test_full_source_smoke.py`

**Steps:**

1. Add a smoke test that can be run locally against the full source folder.
2. Run:

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source --source "D:\OneDrive\Dokumente\CM History"
.\.venv\Scripts\python -m cm_dashboard.cli import --source "D:\OneDrive\Dokumente\CM History" --db "data\cardmarket.db"
.\.venv\Scripts\python -m cm_dashboard.cli validate --db "data\cardmarket.db"
```

Expected: import completes; validation reports known warnings but no critical parser crash.

3. Commit:

```powershell
git add src tests
git commit -m "Verify importer against full source folder"
```

**Acceptance:** All current files are importable or explicitly reported with source-backed reasons.

### Task 22: Add Reporting Query Layer

**Objective:** Create stable read queries for dashboard and reports.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\reporting\__init__.py`
- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\reporting\queries.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_reporting_queries.py`

**Steps:**

1. Add tests for date range, direction, date basis, product, expansion, category, username, country, and order filters.
2. Add tests for monthly aggregation and period totals.
3. Implement read-only SQL queries.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_reporting_queries.py
```

Expected: reporting query tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\reporting tests\test_reporting_queries.py
git commit -m "Add dashboard reporting queries"
```

**Acceptance:** UI can be built on tested query outputs instead of ad hoc SQL.

### Task 23: Add Local Web App Shell

**Objective:** Create the browser entry point and base layout.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\__init__.py`
- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\base.html`
- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\static\app.css`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_web_app.py`

**Steps:**

1. Add tests for app startup and base route response.
2. Implement FastAPI app factory and base template.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_web_app.py
```

Expected: app shell tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\web tests\test_web_app.py
git commit -m "Add local dashboard web shell"
```

**Acceptance:** A local page can load without requiring import UI features yet.

### Task 24: Add Import Status Page

**Objective:** Show imported files, counts, warnings, and validation issues.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\imports.html`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_import_status_page.py`

**Steps:**

1. Add tests for import file list, issue severity, and source metadata display.
2. Implement `/imports`.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_import_status_page.py
```

Expected: import status page tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\web tests\test_import_status_page.py
git commit -m "Show import status and validation issues"
```

**Acceptance:** The user can see whether data is trustworthy before reading reports.

### Task 25: Add Dashboard Summary Page

**Objective:** Show the first practical KPIs and simple charts.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\dashboard.html`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\static\app.js`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_dashboard_page.py`

**Steps:**

1. Add tests for date-range filter handling and KPI rendering.
2. Add monthly purchase/sales totals and shipment/article counts.
3. Add one simple chart with accessible table fallback.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_dashboard_page.py
```

Expected: dashboard tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\web tests\test_dashboard_page.py
git commit -m "Add MVP dashboard summary"
```

**Acceptance:** The first screen answers period performance at a glance.

### Task 26: Add Shipment Explorer

**Objective:** Let the user filter and inspect normalized orders.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\shipments.html`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_shipments_page.py`

**Steps:**

1. Add tests for date, direction, date basis, username, country, and order filters.
2. Implement shipment list with masked personal fields by default.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_shipments_page.py
```

Expected: shipment explorer tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\web tests\test_shipments_page.py
git commit -m "Add shipment explorer"
```

**Acceptance:** Orders can be found by the core business filters.

### Task 27: Add Shipment Detail Page

**Objective:** Show one order with linked article lines and source traceability.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\shipment_detail.html`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_shipment_detail_page.py`

**Steps:**

1. Add tests for order details, linked article lines, shipment totals, and source file/row references.
2. Implement `/shipments/{order_id}`.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_shipment_detail_page.py
```

Expected: shipment detail tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\web tests\test_shipment_detail_page.py
git commit -m "Add linked shipment detail view"
```

**Acceptance:** Related records are genuinely connected in the UI.

### Task 28: Add Article Explorer

**Objective:** Let the user filter article lines by card/product attributes.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\articles.html`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_articles_page.py`

**Steps:**

1. Add tests for product ID/name, article text, expansion, category, direction, and date range filters.
2. Implement article-line table with link to shipment detail.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_articles_page.py
```

Expected: article explorer tests pass.

4. Commit:

```powershell
git add src\cm_dashboard\web tests\test_articles_page.py
git commit -m "Add article explorer filters"
```

**Acceptance:** The user can answer which articles/cards were bought or sold in a period.

### Task 29: Add Product Detail Page

**Objective:** Aggregate all observed labels and article lines for one product ID.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\product_detail.html`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_product_detail_page.py`

**Steps:**

1. Add tests for multiple localized labels on one product ID.
2. Add tests for buy/sell totals and linked article lines.
3. Implement `/products/{product_id}`.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_product_detail_page.py
```

Expected: product detail tests pass.

5. Commit:

```powershell
git add src\cm_dashboard\web tests\test_product_detail_page.py
git commit -m "Add product detail aggregation"
```

**Acceptance:** Localized product-name drift does not hide product history.

### Task 30: Add Period Report Export

**Objective:** Provide a simple date-range report that can be downloaded as CSV.

**Files:**

- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\reporting\queries.py`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\app.py`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_period_report_export.py`

**Steps:**

1. Add tests for report filters and CSV output headers.
2. Implement a CSV response for period totals and grouped monthly rows.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_period_report_export.py
```

Expected: period report tests pass.

4. Commit:

```powershell
git add src\cm_dashboard tests\test_period_report_export.py
git commit -m "Add period report CSV export"
```

**Acceptance:** Reports can be archived outside the app without PDF complexity.

### Task 31: Add Privacy Controls for Detail Fields

**Objective:** Ensure personal address/name/VAT data is not exposed by accident.

**Files:**

- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\reporting\queries.py`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\shipments.html`
- Modify `D:\OneDrive\Dokumente\CM History\src\cm_dashboard\web\templates\shipment_detail.html`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_privacy_masking.py`

**Steps:**

1. Add tests that list pages mask address/name/VAT details by default.
2. Add a local-only explicit reveal flag for detail pages if approved.
3. Run:

```powershell
.\.venv\Scripts\python -m pytest tests\test_privacy_masking.py
```

Expected: masking tests pass.

4. Commit:

```powershell
git add src\cm_dashboard tests\test_privacy_masking.py
git commit -m "Mask personal shipment details by default"
```

**Acceptance:** Sensitive source data is not casually exposed in normal dashboard use.

### Task 32: Add Monthly Import Workflow Documentation

**Objective:** Explain how future monthly exports are added and validated.

**Files:**

- Modify `D:\OneDrive\Dokumente\CM History\README.md`
- Create `D:\OneDrive\Dokumente\CM History\docs\monthly_import.md`

**Steps:**

1. Document where to place new files.
2. Document inspect, import, validate, and app start commands.
3. Explain duplicate and missing-period warnings in user-facing language.
4. Run:

```powershell
.\.venv\Scripts\python -m pytest
```

Expected: tests still pass.

5. Commit:

```powershell
git add README.md docs\monthly_import.md
git commit -m "Document monthly import workflow"
```

**Acceptance:** A future month can be imported by following the docs.

### Task 33: Add End-to-End Smoke Verification

**Objective:** Bundle the MVP verification path into one repeatable check.

**Files:**

- Create `D:\OneDrive\Dokumente\CM History\scripts\verify_mvp.ps1`
- Create `D:\OneDrive\Dokumente\CM History\tests\test_verify_script_documented.py`

**Steps:**

1. Add a script that runs tests, lint, source inspection, import, and validation.
2. Add a test or documentation check that the script exists and references the expected commands.
3. Run:

```powershell
.\scripts\verify_mvp.ps1
```

Expected: all checks pass or validation reports only accepted known warnings.

4. Commit:

```powershell
git add scripts\verify_mvp.ps1 tests\test_verify_script_documented.py
git commit -m "Add MVP verification script"
```

**Acceptance:** A single command proves the MVP is ready to review.

### Task 34: Final MVP Review Pass

**Objective:** Confirm the implemented product matches the reduced MVP and does not include deferred scope.

**Files:**

- Modify only docs or tests if gaps are found.

**Steps:**

1. Run:

```powershell
.\scripts\verify_mvp.ps1
```

Expected: verification passes.

2. Manually open the app:

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app --reload
```

Expected: dashboard, import status, shipment explorer, article explorer, detail pages, and CSV export work locally.

3. Commit:

```powershell
git add README.md docs src tests scripts migrations
git commit -m "Finalize Cardmarket dashboard MVP"
```

**Acceptance:** All MVP acceptance criteria are demonstrably met and non-goals remain out of scope.

## Suggested Task Order

1. Project foundation: Tasks 1-3.
2. Source understanding in code: Tasks 4-11.
3. Database and import pipeline: Tasks 12-21.
4. Reporting/query layer: Task 22.
5. Web dashboard: Tasks 23-31.
6. Documentation and final verification: Tasks 32-34.

Do not start UI pages before Tasks 4-21 are stable. The feasibility review shows that the main risk is import correctness, not page rendering.

## Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---:|---|
| XLS parser corrupts Unicode or fails on older XLS files. | High | Add parser fixture tests before importer work; switch parser approach if fidelity fails. |
| Shipment grouped rows are treated as separate orders or dropped. | High | Store raw rows and test forward-filled `resolved_order_id` counts against known evidence. |
| CSV/XLS duplicate exports double-count sales. | High | Generate business keys and validate duplicate overlap before aggregation. |
| Purchase-date and payment-date exports are mixed into one date field. | High | Model date basis and shipment events explicitly. |
| Missing monthly coverage creates misleading reports. | High | Show coverage gaps in import validation and dashboard warnings. |
| Product localized names overwrite each other. | Medium | Store observed labels separately from stable product IDs. |
| Address/name/VAT data appears in normal dashboard lists. | Medium | Mask sensitive fields by default and test this behavior. |
| UI work starts before data trust exists. | Medium | Gate UI tasks behind full import and validation. |
| The PRD's broader reporting/charting ambitions expand MVP scope. | Medium | Limit MVP to basic period reports and simple charts. |
| SQLite becomes limiting later. | Low | Keep SQL isolated behind query/repository functions for later migration. |

## Human Approval Gates

| Gate | Needed Before | Decision Required |
|---|---|---|
| Local-only architecture approval | Task 1 | Confirm no public hosting or multi-user auth is required for MVP. |
| Python/FastAPI/SQLite approval | Task 1 | Confirm the proposed stack is acceptable. |
| Source folder handling approval | Task 3 | Confirm tests may reference real local XLS/CSV files by path without copying them. |
| Parser choice approval | Task 7 if Unicode/tolerant parsing requires a heavier dependency | Confirm acceptable parser dependency or conversion approach. |
| Privacy display approval | Task 31 | Decide whether detail pages may reveal full personal/address/VAT data locally. |
| MVP scope approval | Before Task 23 | Confirm UI should remain limited to dashboard, import status, shipment explorer, article explorer, details, and CSV export. |

## Final Readiness Checklist

- [ ] Project skeleton exists and installs locally.
- [ ] Source scanner classifies all current XLS/CSV files.
- [ ] XLS reader passes tolerant-parser fixture.
- [ ] Unicode fidelity fixture passes.
- [ ] CSV reader imports current CSV files.
- [ ] Raw staging stores every source row with file and row traceability.
- [ ] Shipment continuation rows are forward-filled and tested.
- [ ] Article and shipment records are linked by order ID.
- [ ] Duplicate CSV/XLS pairs are detected and not double-counted.
- [ ] Purchase-date and payment-date facts remain distinguishable.
- [ ] Missing monthly coverage is visible in validation output.
- [ ] Product IDs support multiple observed localized labels.
- [ ] Full source-folder import completes.
- [ ] Validation reports known warnings and no critical importer failure.
- [ ] Dashboard filters cover date, direction, date basis, order, product, expansion, category, username, and country.
- [ ] Period report and CSV export work.
- [ ] Basic monthly charts render.
- [ ] Sensitive personal fields are masked by default.
- [ ] README explains monthly import workflow.
- [ ] `pytest` passes.
- [ ] `ruff check src tests` passes.
- [ ] MVP verification script passes.
- [ ] Deferred features remain out of the MVP.
