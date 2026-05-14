# NCAA Report Tool Optimization Implementation Plan

## Purpose

This document turns `OPTIMIZATION_AUDIT.md` into an implementation roadmap. The goal is to improve runtime performance, reduce duplicated code, make the project easier to package, and create a cleaner foundation for future features.

The plan is intentionally staged. Each phase should leave the application usable, with the four current workflows still available:

- Scholarship reports
- Sport operating budget reports
- Revenue reports
- Total operating expenses reports

## Guiding Principles

- Preserve current report outputs unless a change is explicitly marked as a behavior change.
- Optimize PDF reads first because PDF parsing is the most expensive operation in the app.
- Centralize duplicated helpers before doing larger refactors.
- Keep report-specific extraction logic separate from shared UI, PDF, Excel, and sport utilities.
- Add small verification checks after each phase instead of waiting until the end.
- Avoid changing packaged artifacts while refactoring source code.

## Phase 0: Safety, Baseline, and Project Hygiene

### Goals

- Establish a safe working baseline before changing program behavior.
- Make it clear which files are source code and which files are generated output.
- Capture current behavior so later changes can be compared.

### Implementation Tasks

1. Create a manual backup or initialize Git.
   - This folder currently does not appear to be a Git repository.
   - Recommended: initialize a Git repository before major refactors.
   - If Git is not desired, make a timestamped copy of the source-only files.

2. Add a `.gitignore` if using Git.
   - Ignore generated files and local metadata:

```gitignore
__pycache__/
*.py[cod]
build/
dist/
*.dmg
*.zip
*.app/
.DS_Store
.idea/
testoutputs1/
```

3. Record a current file inventory.
   - Source areas:
     - `__main__.py`
     - `saui.py`
     - `rev/`
     - `sportops/`
     - `scholar/`
     - `toe/`
     - `__main__.spec`
   - Documentation:
     - `PROJECT_REPORT.md`
     - `OPTIMIZATION_AUDIT.md`
     - `IMPLEMENTATION_PLAN.md`
   - Generated or release output:
     - `build/`
     - `dist/`
     - `__pycache__/`
     - `.dmg` files
     - release `.zip` files
     - `testoutputs1/`

4. Capture manual baseline behavior.
   - Run each workflow with a known folder of PDFs.
   - Save one output workbook per workflow.
   - Record:
     - approximate processing time
     - number of PDFs selected
     - number of skipped files
     - generated workbook sheet names
     - whether formulas and formatting open correctly in Excel

### Acceptance Criteria

- There is a rollback path before source changes begin.
- Generated artifacts are identified and ignored or excluded from source-focused work.
- At least one known-good output workbook exists for comparison per workflow.

## Phase 1: Low-Risk Cleanup

### Goals

- Remove obvious maintainability issues without changing core report logic.
- Make later refactors easier to review.

### Implementation Tasks

1. Remove unused imports.
   - Example: `time` in `saui.py` appears unused.
   - Check each package for unused imports after replacing wildcard imports later.

2. Remove or gate debug prints.
   - Current examples:
     - full dictionary prints in `scholar/extract_scholarships.py`
     - table dictionary prints in `sportops/Folder_Parser.py`
     - parsed revenue list prints in `rev/Folder_Parser.py`
   - Replace with a simple `verbose=False` option or a shared logger.

3. Move module-level sample data out of production modules.
   - `rev/Data_Processing.py` contains sample `df_21`, `df_27`, and `data_40`.
   - Move these into a future test file or an examples document.

4. Standardize report status messages.
   - Use consistent terms:
     - "processed"
     - "skipped"
     - "not readable"
     - "no matching section"
   - Avoid only printing skipped files to terminal because packaged desktop users may never see stdout.

5. Create a lightweight `common/` package.
   - Add `common/__init__.py`.
   - Do not migrate all logic yet.
   - This phase just creates the destination for shared utilities.

### Acceptance Criteria

- The launcher still opens.
- Each workflow still reaches folder selection.
- No workbook structure or extraction behavior intentionally changes.
- Debug output is reduced or optional.

## Phase 2: Shared Utilities and Deduplication

### Goals

- Replace duplicated helper files with shared utilities.
- Reduce repeated maintenance across `rev`, `sportops`, `scholar`, and `toe`.

### Proposed Shared Modules

```text
common/
  __init__.py
  pdf_names.py
  pdf_manifest.py
  dialogs.py
  report_log.py
  sports.py
  excel_styles.py
```

### Implementation Tasks

1. Create `common/pdf_names.py`.
   - Move `extract_reporting_institution(...)` into this file.
   - Compile the reporting institution regex once at module load.
   - Keep existing fallback behavior:
     - if extraction fails, use filename without extension
     - remove trailing `, FY24`, `, FY2024`, and similar markers
   - Update all report packages to import from `common.pdf_names`.

2. Create `common/pdf_manifest.py`.
   - Add a function such as `build_pdf_manifest(folder_path)`.
   - Return a list of records with:
     - `path`
     - `filename`
     - `institution_name`
     - `name_source`, such as `pdf` or `filename`
   - Sort records by institution name for consistent dropdown order.

3. Create `common/dialogs.py`.
   - Move shared university selection popup logic here.
   - Move reusable processing modal behavior here if practical.
   - Keep the same UI flow at first to reduce behavior risk.

4. Create `common/report_log.py`.
   - Move skipped-file report writing into one shared helper.
   - Add optional skipped reasons:
     - `not_pdf`
     - `name_not_found`
     - `section_not_found`
     - `parse_error`
     - `empty_result`

5. Create `common/sports.py`.
   - Centralize:
     - men's-only sport list
     - women's-only sport list
     - sport aliases
     - `normalize_sport_name(...)`
   - Replace duplicated lists in Scholarship, Sport Ops, and Revenue.

6. Create `common/excel_styles.py`.
   - Centralize repeated style constants:
     - currency format
     - title fills
     - header fills
     - common borders
     - alignment helpers
   - Adopt this gradually after behavior tests pass.

7. Replace duplicated files.
   - First convert duplicates into compatibility wrappers that import shared functions.
   - After workflows are verified, remove redundant code or leave wrappers only if package imports require them.

### Acceptance Criteria

- All workflows use one shared university-name extractor.
- All workflows use one shared skipped-file writer.
- Repeated sport gender lists are sourced from one place.
- Existing user flow remains recognizable.
- Manual workflow outputs match baseline for the same sample PDFs.

## Phase 3: PDF Read Optimization

### Goals

- Reduce the number of times each PDF is opened.
- Speed up large folder processing.

### Implementation Tasks

1. Use the PDF manifest in all UIs.
   - Current workflow:
     - UI scans folder and extracts names.
     - parser scans folder again and extracts names again.
   - New workflow:
     - UI builds `manifest`.
     - dropdown uses `manifest.institution_name`.
     - processing receives `manifest`.

2. Update processing functions to accept manifest records.
   - Scholarship:
     - change `process_folder(folder_path, exclude_list)` to accept optional `manifest`.
     - use `record.path` and `record.institution_name`.
   - Sport Ops:
     - change `collect_sports_across_pdfs(folder_path)` to accept optional `manifest`.
   - Revenue:
     - change `collect_revenue_across_pdfs(folder_path)` to accept optional `manifest`.
   - TOE:
     - change `parse_folder_toe(folder_path, client_uni)` to accept optional `manifest`.

3. Avoid reopening PDFs for name extraction.
   - Once `institution_name` is on the manifest, do not call `extract_reporting_institution(...)` again inside processing loops.

4. Consider page text caching for extraction-heavy workflows.
   - For Sport Ops, cache page text and structural tables per page.
   - For TOE, cache extracted text or pass text into the regex extractor.
   - For Revenue, cache summary text if `extract_summary_totals(...)` can be refactored cleanly.

5. Add timing logs.
   - Record total workflow time.
   - Record per-PDF extraction time.
   - Keep logs optional and user-friendly.

### Acceptance Criteria

- Each workflow opens each PDF for name extraction at most once.
- Processing no longer repeats university-name extraction.
- Outputs match baseline workbooks for known sample folders.
- Large folder processing is measurably faster or at least no slower.

## Phase 4: Data Processing and Excel Optimization

### Goals

- Reduce pandas overhead.
- Make Excel generation easier to maintain.
- Keep report formulas and formatting intact.

### Implementation Tasks

1. Replace `iterrows()` where practical.
   - Use `itertuples(index=False)` in:
     - `scholar/fill_excel_with_data_scholar.py`
     - `sportops/fill_excel_with_data_sportops.py`
     - `rev/fill_excel_with_data_revenue.py`
   - For loops that need index labels, use `itertuples()` with explicit index or precomputed tuples.

2. Vectorize filtering.
   - Replace repeated `apply(lambda x: ...)` filters with vectorized string operations where possible.
   - Precompile repeated regex patterns.

3. Separate Excel responsibilities.
   - Current TOE PDF parsing, template generation, and fill logic are all in `toe/data_extraction.py`.
   - Split into:
     - `toe/extraction.py`
     - `toe/excel_template.py`
     - `toe/fill_excel.py`
   - Apply similar separation to other reports only if it reduces confusion.

4. Centralize formula generation.
   - Create helpers for:
     - average formula
     - median formula
     - rank formula
     - include-client versus exclude-client range behavior

5. Reuse style objects.
   - Avoid recreating identical `Font`, `PatternFill`, `Alignment`, and `Border` objects across files.
   - Keep style definitions in `common/excel_styles.py`.

### Acceptance Criteria

- Generated workbooks still open in Excel.
- Formulas still calculate correctly.
- Client row, average row, median row, and rank row are preserved.
- Worksheet names and order remain unchanged unless intentionally improved.

## Phase 5: Sport Ops Table Extraction Refactor

### Goals

- Make the slowest and most complex extraction path easier to reason about.
- Reduce repeated table detection work.

### Implementation Tasks

1. Create a table configuration.
   - Move Sport Ops table metadata out of inline lists.
   - Include:
     - table number
     - display name
     - expected header words
     - aliases
     - whether fallback parsing is allowed

2. Cache page-level extraction.
   - For each page:
     - extract text once
     - split lines once
     - create normalized line variants once
     - call `page.find_tables()` once

3. Match titles and tables after page extraction.
   - Current extraction may call structural table detection inside title loops.
   - New flow should:
     - find all candidate titles on the page
     - find all structural tables on the page
     - associate tables with nearest candidate title
     - fallback to line parsing only when needed

4. Isolate fallback parser.
   - Move regex row parsing into a pure function that accepts lines.
   - Add tests using text fixtures rather than requiring full PDFs.

5. Improve skipped reasons.
   - Replace generic return value `1` with structured results:
     - success with tables
     - no text
     - no matching table titles
     - table parse failure

### Acceptance Criteria

- Sport Ops output matches baseline for known PDFs.
- Failed PDFs produce clearer skipped reasons.
- Per-page table detection happens once.
- Fallback parser can be tested without opening a PDF.

## Phase 6: Revenue and Ticket Sales Configuration

### Goals

- Make Revenue parsing easier to maintain.
- Treat Ticket Sales as an explicit first-class metric.

### Implementation Tasks

1. Create `rev/config.py`.
   - Define revenue source tables:

```python
REVENUE_TABLES = {
    "1": {"label": "Ticket Sales", "required": True},
    "2": {"label": "Direct State or Other"},
    "3": {"label": "Student Fees"},
    "4": {"label": "Direct Institutional"},
    "7": {"label": "Guarantees"},
    "8": {"label": "Contributions"},
    "11": {"label": "Media Rights"},
    "12": {"label": "NCAA Distributions"},
    "13": {"label": "Conference Distributions"},
    "13A": {"label": "Football Bowl Generated Revenue"},
    "14": {"label": "Program, Novelty, Parking and Concession Sales"},
    "15": {"label": "Royalties, Licensing, Advertisement and Sponsorships"},
    "18": {"label": "Other Operating"},
    "19": {"label": "Football Bowl"},
}
```

2. Define combination rules explicitly.

```python
REVENUE_COMBINATIONS = {
    "2": ["2", "4"],
    "12": ["12", "13"],
    "16": ["13A", "19"],
}
```

3. Add validation.
   - After parsing each PDF, track:
     - found tables
     - missing expected tables
     - missing Ticket Sales
     - parse errors

4. Improve output reporting.
   - Add a parse summary that distinguishes:
     - true zero
     - missing table
     - skipped PDF
   - This is especially useful for Ticket Sales because a missing value and zero value can mean very different things.

### Acceptance Criteria

- Revenue output remains consistent with baseline.
- Ticket Sales parsing status is visible in logs or skipped-file report.
- Revenue table labels and combination rules are no longer scattered across processing files.

## Phase 7: Testing and Quality Checks

### Goals

- Add enough testing to make future refactors safer.
- Focus tests on pure functions and output invariants.

### Recommended Tests

1. PDF name extraction tests.
   - Input: first-page and second-page text samples.
   - Expected: correct institution name.
   - Include fallback cases.

2. Sport normalization tests.
   - Track and field variants become `XC/TF`.
   - Swimming variants become `Swimming and Diving`.
   - Acrobatics variants become `Acrobatics and Tumbling`.
   - Soccer variants normalize consistently.

3. Revenue combination tests.
   - Columns `2` and `4` combine into `2`.
   - Columns `12` and `13` combine into `12`.
   - Columns `13A` and `19` combine into `16`.
   - Missing optional source columns do not crash.

4. TOE regex tests.
   - Valid text returns an integer.
   - Missing section returns `None`.
   - Comma-formatted values parse correctly.

5. Excel formula tests.
   - Include-client formulas use the client row in average and median.
   - Exclude-client formulas omit the client row from average and median.
   - Rank still compares client against the full peer range.

6. Sport Ops fallback parser tests.
   - Text lines parse into category, men, women, and not allocated.
   - Total rows and unrelated rows are excluded.
   - Gender keyword assignment works for single-value rows.

### Acceptance Criteria

- Tests can run without opening the Tkinter UI.
- Pure function tests do not require real PDFs when text fixtures are enough.
- At least one manual end-to-end test remains for each report workflow.

## Phase 8: Packaging Improvements

### Goals

- Make the app easier to build and distribute.
- Keep release artifacts separate from source.

### Implementation Tasks

1. Review `__main__.spec`.
   - Confirm the app name, icon, bundle identifier, hidden imports, and output paths.
   - Avoid bundling accidental generated files.

2. Create a build script.
   - Example:
     - `scripts/build_macos.sh`
     - `scripts/build_windows.ps1`
   - Each script should:
     - clean previous build output
     - run PyInstaller
     - move release output into a release folder

3. Add release notes template.
   - Include:
     - version
     - date
     - changed workflows
     - known limitations
     - testing performed

4. Separate test outputs from generated release outputs.
   - Move intentional sample files into `tests/fixtures/`.
   - Move generated test workbooks into an ignored temp/output directory.

### Acceptance Criteria

- Build output does not clutter source folders.
- Release artifacts are reproducible.
- App can still be launched from source with `python -m programlauncher` or the current equivalent.

## Proposed Future Features

### 1. Batch summary dashboard

Add a final summary window after report generation showing:

- number of PDFs found
- number processed successfully
- number skipped
- skipped-file reasons
- output workbook path
- processing duration

Why it helps:

Users get confidence that the report completed correctly without opening terminal output.

### 2. Detailed skipped-file report

Enhance the current skipped-file report to include:

- file name
- institution name if available
- workflow
- reason skipped
- extraction stage where failure occurred
- suggested next action

Why it helps:

This turns parse failures into actionable review items.

### 3. Preview before saving

Show a lightweight preview before workbook generation:

- selected client
- include/exclude client setting
- detected peer institutions
- detected male/female sports
- missing expected categories

Why it helps:

Users can catch wrong client selection or missing PDFs before generating a workbook.

### 4. Recent folders and default save location

Remember:

- last selected PDF folder
- last save directory
- last client include/exclude choice

Why it helps:

Repeated report generation becomes faster for users working with the same NCAA folder.

### 5. Per-report progress details

Replace the generic "Processing..." message with details such as:

- current PDF count
- current institution
- current extraction stage
- skipped count so far

Why it helps:

Large folders feel less frozen and users can see progress.

### 6. Cancel processing

Add a safe cancel button during long processing.

Expected behavior:

- stop after the current PDF finishes
- close progress window
- show partial processing summary
- do not write an incomplete workbook unless the user confirms

Why it helps:

Users can recover from selecting the wrong folder without force-quitting the app.

### 7. Configurable sport aliases

Move sport alias rules into a user-editable config file.

Examples:

- Track and Field variants -> `XC/TF`
- Swimming variants -> `Swimming and Diving`
- Acrobatics variants -> `Acrobatics and Tumbling`

Why it helps:

Users can adjust naming without editing Python code when NCAA formatting changes.

### 8. Revenue/Ticket Sales validation report

Add a Revenue-specific validation sheet or summary that shows:

- whether Ticket Sales was found for each institution
- missing revenue categories
- categories combined into final metrics
- true zero versus missing parse result

Why it helps:

Ticket Sales and revenue categories are high-value fields where silent missing data can be misleading.

### 9. Built-in output comparison tool

Add a developer/admin tool that compares two generated workbooks.

Compare:

- sheet names
- row/column counts
- formulas
- values
- missing institutions
- changed sport columns

Why it helps:

This makes refactoring safer because new output can be compared against baseline output.

### 10. Settings file

Add a small settings file for persistent app preferences:

- default include-client setting
- default save folder
- verbose logging enabled or disabled
- custom sport aliases
- preferred output filename pattern

Why it helps:

Reduces repeated user choices and allows future features without hardcoding behavior.

### 11. Structured logging

Add a log file per run.

Include:

- app version
- timestamp
- selected workflow
- selected folder
- processing duration
- skipped files
- exceptions

Why it helps:

Debugging packaged desktop issues becomes much easier.

### 12. Automated update/version check

Add optional version metadata and a manual "Check for Updates" action.

Why it helps:

Users can tell whether they are running the latest release without inspecting installer filenames.

### 13. Report templates by client or conference

Allow reusable template presets:

- title text
- conference name
- color palette
- included sports
- output naming convention

Why it helps:

The same tool can support multiple client styles without editing Excel generator code.

### 14. Headless command-line mode

Add optional CLI usage for repeatable processing:

```bash
python -m programlauncher --report revenue --folder ./pdfs --client "Example University" --include-client yes --output ./revenue.xlsx
```

Why it helps:

Enables automation, testing, and faster internal workflows without clicking through the UI.

### 15. Input PDF quality checker

Before extraction, scan PDFs for basic quality signals:

- no extractable text
- missing first two pages
- reporting institution not found
- expected NCAA section headings missing

Why it helps:

Users get early warnings when PDFs are scanned images or wrong report files.

## Recommended Execution Order

1. Phase 0: establish safety and baseline.
2. Phase 1: clean low-risk debug and sample code.
3. Phase 2: add shared utilities and remove duplication.
4. Phase 3: implement PDF manifest and reduce repeated PDF opens.
5. Phase 4: optimize pandas and Excel write paths.
6. Phase 6: improve Revenue/Ticket Sales configuration.
7. Phase 5: refactor Sport Ops table extraction.
8. Phase 7: add tests around pure logic and workbook formulas.
9. Phase 8: clean packaging and release flow.

Sport Ops is listed after Revenue configuration because it has the highest extraction complexity and should be refactored after the shared PDF and testing foundation exists.

## Definition of Done

The optimization work should be considered complete when:

- All four workflows still generate valid Excel workbooks.
- PDF institution names are extracted once per workflow run and reused.
- Duplicated helper modules are centralized or reduced to compatibility wrappers.
- Revenue/Ticket Sales rules are explicit and easier to validate.
- Sport Ops extraction has clearer table parsing structure and skipped reasons.
- Generated artifacts are excluded from the source-focused project tree.
- There are tests for shared parsing, normalization, and formula logic.
- The app has a clear path for future features without duplicating code across report packages.

