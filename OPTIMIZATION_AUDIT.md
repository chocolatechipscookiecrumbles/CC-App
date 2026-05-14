# NCAA Report Tool Optimization Audit

## Executive Summary

This audit identifies the main places where the NCAA Report Tool can be made faster, easier to maintain, and cleaner to package. The highest-value improvements are not small syntax changes. They are structural optimizations around PDF processing, repeated shared code, pandas row loops, and project hygiene.

The biggest runtime opportunity is reducing repeated PDF reads. Several workflows open the same PDF once to extract the reporting institution name and then again to extract the actual report data. Since PDF text extraction is one of the slowest operations in this program, caching each file's extracted text and institution name should noticeably reduce processing time for large folders.

The biggest organization opportunity is consolidating duplicated modules. Files such as `getname.py`, `choose_uni.py`, `checklist.py`, `include_client.py`, and `write_report.py` are duplicated across report packages. This makes every future fix slower because the same change may need to be copied into multiple places.

The biggest packaging cleanup is separating source code from generated build artifacts. The project folder currently includes `dist/`, `build/`, `__pycache__/`, large `.dmg` installers, zipped apps, test output spreadsheets, and IDE metadata. These files increase folder size dramatically and make it harder to see the real source of the application.

Recommended implementation order:

1. Add shared utilities for PDF discovery, university-name extraction, skipped-file reporting, and common Tkinter dialogs.
2. Cache PDF text and reporting institution names during each workflow so each PDF is opened as few times as possible.
3. Replace pandas `iterrows()` loops where practical with `itertuples()`, vectorized operations, or bulk worksheet writes.
4. Move duplicated report configuration into shared constants or per-report config dictionaries.
5. Clean packaging artifacts out of the source directory and add a source-focused project layout.

## Highest Priority Optimizations

### 1. Avoid opening the same PDF multiple times

Priority: High  
Affected areas: `scholar/ui.py`, `scholar/extract_scholarships.py`, `sportops/Folder_Parser.py`, `sportops/Table_Extractor.py`, `rev/Folder_Parser.py`, `rev/Testextract.py`, `toe/data_extraction.py`, all `getname.py` files  
Expected benefit: Faster folder processing, especially for large PDF batches

Current pattern:

- The UI loops through PDFs to build the university dropdown.
- Each file is opened by `extract_reporting_institution(...)`.
- The selected workflow later opens the same PDF again to extract scholarship, sport operating, revenue, or TOE values.
- Some workflows call `extract_reporting_institution(...)` inside the processing loop even after names were already collected for the dropdown.

Why it matters:

PDF parsing is expensive compared with normal text or DataFrame processing. Opening every PDF twice can make total runtime close to `2N` PDF reads for `N` files before counting page-level table extraction. For Sport Ops and Revenue, this cost compounds because table parsing and regex scanning are also performed after name extraction.

Recommended fix:

- Add a shared PDF manifest helper that scans the folder once and returns records such as:
  - `path`
  - `filename`
  - `institution_name`
  - optional cached first-page and second-page text
- Use that manifest in the dropdown and in the report processing step.
- For workflows that need full document text, cache page text once per PDF during processing and pass it into extractors instead of reopening the file for each helper.
- Keep filename fallback behavior for PDFs where the reporting institution cannot be extracted.

Complexity impact:

- Current: roughly `O(N * repeated_pdf_open_cost + N * extraction_cost)`.
- Improved: roughly `O(N * single_pdf_open_cost + N * extraction_cost)`.
- Big-O remains linear in number of PDFs, but the constant factor drops significantly because PDF I/O and text extraction are the slowest operations.

### 2. Consolidate duplicated shared modules

Priority: High  
Affected areas: `rev/`, `sportops/`, `scholar/`, `toe/`  
Expected benefit: Less code to maintain, fewer inconsistent bug fixes, simpler future optimization

Duplicated or near-duplicated files:

- `getname.py`
- `choose_uni.py`
- `include_client.py`
- `write_report.py`
- `checklist.py` in `rev`, `sportops`, and `scholar`
- `main.py` wrappers in several packages

Why it matters:

When the same helper exists in four places, every bug fix has four possible locations. For example, if university-name extraction is optimized or made more accurate, each package-specific `getname.py` copy must be updated. If one copy is missed, workflows will behave differently.

Recommended fix:

- Create a shared package such as `common/` or `shared/`.
- Move generic helpers into shared modules:
  - `common/pdf_names.py` for `extract_reporting_institution`
  - `common/dialogs.py` for university selection and include-client UI
  - `common/report_log.py` for skipped-file report writing
  - `common/checklist.py` for reusable checklist popups
- Keep report-specific logic inside each report package.
- Replace duplicated files with imports from the shared package, then delete the redundant copies after testing.

Complexity impact:

- Runtime complexity does not change directly.
- Maintenance complexity drops from "change up to 4 files" to "change 1 shared helper".

### 3. Replace row-wise pandas loops in hot paths

Priority: High  
Affected areas: `sportops/fill_excel_with_data_sportops.py`, `scholar/fill_excel_with_data_scholar.py`, `rev/fill_excel_with_data_revenue.py`, `sportops/Folder_Parser.py`, `rev/Data_Processing.py`  
Expected benefit: Faster processing and cleaner code for larger DataFrames

Current examples:

- `df.iterrows()` is used in Excel fill paths.
- `sportops/Folder_Parser.py` iterates over DataFrame rows after setting `category` as the index.
- `rev/Data_Processing.py` uses row iteration in misattribution analysis and other candidate row logic.

Why it matters:

`iterrows()` is one of the slower pandas iteration methods because each row becomes a Series. In Excel-writing code, the worksheet write itself is often the bottleneck, but using `itertuples()` still reduces overhead and makes row access more predictable. In data-processing code, vectorized filtering and aggregation can be much faster and easier to reason about.

Recommended fix:

- Use `itertuples()` for worksheet population when row-by-row writes are necessary.
- Use vectorized pandas operations for filtering, numeric conversion, and column summation.
- Where openpyxl writes many cells, consider preparing rows as plain tuples and appending or assigning in tight loops.
- Keep formatting loops separate from value-writing loops so styles are not recalculated repeatedly.

Complexity impact:

- Current row-wise processing is usually `O(R * C)` but with high pandas object overhead.
- Improved processing is still often `O(R * C)`, but with lower overhead through tuple iteration, vectorized operations, and fewer per-cell style calculations.

### 4. Refactor Sport Ops table extraction to reduce repeated scanning

Priority: High  
Affected areas: `sportops/Table_Extractor.py`, `sportops/Folder_Parser.py`  
Expected benefit: Faster Sport Ops report generation and easier debugging of table extraction failures

Current pattern:

- Each page's text is split into lines.
- The extractor scans lines for table titles.
- For each possible title, it may call `page.find_tables()`.
- If structural extraction fails, it scans following lines with regex fallbacks.

Why it matters:

Sport Ops appears to have the most complex extraction path. The combination of page text extraction, repeated line scanning, structural table detection, and fallback parsing can become expensive. It is also difficult to isolate whether slowdowns are from PDF layout detection or text fallback parsing.

Recommended fix:

- Precompute normalized page text and line variants once per page.
- Call `page.find_tables()` once per page, not inside every title match.
- Build a page-level table cache and match extracted tables to nearby title sections.
- Move table metadata into a configuration structure with table number, title, aliases, and parsing rules.
- Add timing logs around each PDF and each extraction strategy so slow PDFs can be identified.

Complexity impact:

- Current worst case can approach `O(P * T * table_detection_cost)` where `P` is pages and `T` is title matches.
- Improved approach should be closer to `O(P * table_detection_cost + P * line_scan_cost)`.

### 5. Clean project packaging artifacts out of source

Priority: High  
Affected areas: root folder, `dist/`, `build/`, `__pycache__/`, `testoutputs1/`, `.idea/`, large `.dmg` and `.zip` files  
Expected benefit: Smaller project, easier navigation, faster searches, simpler handoff

Current project hygiene issues:

- `dist/` contains packaged `.app` bundles and dependency trees.
- `build/` contains PyInstaller build output.
- `__pycache__/` directories are present in root and report packages.
- Large installer files such as `.dmg` archives live in the source folder.
- Test output spreadsheets are stored in `testoutputs1/`.
- IDE metadata is present in `.idea/`.

Why it matters:

Generated files make the project harder to inspect. They also slow broad file searches and can confuse future maintainers about what is source versus output. The project folder is also several gigabytes larger than the actual source code.

Recommended fix:

- Keep generated packages outside the source tree or in a clearly ignored release folder.
- Add a `.gitignore` if this project becomes a Git repository.
- Ignore or remove from source control:
  - `build/`
  - `dist/`
  - `__pycache__/`
  - `*.pyc`
  - `*.dmg`
  - packaged `.app` bundles
  - generated `.zip` releases
  - `.idea/`
  - test output spreadsheets unless intentionally used as fixtures
- Keep only source files, configuration, documentation, and intentional sample fixtures in the main project.

## Time Complexity and Runtime Hotspots

### PDF folder scans

Affected areas: all report workflows  
Expected benefit: Reduce repeated I/O and repeated string cleanup

Each workflow scans the selected folder with `os.listdir(...)`. This is fine because folder listing is linear and cheap. The optimization target is not the list operation itself. The target is what happens inside each loop: opening PDFs, extracting text, and parsing pages.

Recommended improvements:

- Use one shared folder scan function that returns sorted PDF paths.
- Store both file path and extracted institution name.
- Avoid repeated `os.path.join(folder_path, filename)` calls throughout the same loop by creating a `pdf_path` variable once.
- Sort records once for consistent UI and report ordering.

### University name extraction

Affected areas: all `getname.py` files and all workflow UIs  
Expected benefit: Faster startup before the client university dropdown appears

`extract_reporting_institution(...)` opens the PDF and extracts text from the first two pages. The same logic is duplicated across packages. It should be shared and cached.

Recommended improvements:

- Compile the reporting institution regex once at module load.
- Make the function accept optional already-extracted page text.
- Cache `(pdf_path, modified_time)` to institution name during a workflow.
- Return structured results such as `name`, `source`, and `error` if more diagnostics are needed.

### Pandas filtering and normalization

Affected areas: `rev/Data_Processing.py`, `sportops/Data_Processing.py`, `scholar/extract_scholarships.py`  
Expected benefit: Better performance on larger report sets and clearer data transformations

Some filtering uses row-wise `apply(lambda ...)` or manual loops. This is acceptable for small datasets, but can be simplified.

Recommended improvements:

- Precompile repeated regex patterns.
- Use vectorized `str.contains(...)`, `str.lower()`, and `str.strip()` where possible.
- Replace manual list deduplication with normalized sets.
- Keep sport normalization rules in one shared mapping or function.

### Excel generation and styling

Affected areas: `Excel_Generator.py`, `build_scholarship_sheet.py`, `fill_excel_with_data_*.py`, `toe/data_extraction.py`  
Expected benefit: Faster workbook generation and less duplicated styling code

Excel writing is naturally cell-oriented, but repeated style creation and repeated formatting loops can still add overhead.

Recommended improvements:

- Reuse style objects instead of recreating similar `Font`, `PatternFill`, `Alignment`, and `Border` objects in multiple files.
- Create common helpers for currency formatting, borders, title rows, average/median/rank rows, and client rows.
- Use `itertuples()` for data writes.
- Separate workbook structure creation from data fill and from styling.

### Subset-sum misattribution correction

Affected areas: `rev/Data_Processing.py`, `sportops/Data_Processing.py`  
Expected benefit: Prevent worst-case slowdown if values or candidate lists grow

The misattribution correction uses dynamic programming for exact subset-sum. This can be useful, but the complexity depends on the target amount, not just the number of rows.

Complexity note:

- Current integer subset-sum is approximately `O(C * target)` where `C` is candidate row count and `target` is the integer amount to balance.
- If `target` is large, this can become expensive even with few rows.

Recommended improvements:

- Add a maximum target threshold for exact DP.
- Fall back to a bounded heuristic when the target is too large.
- Log when correction is skipped or falls back.
- Remove module-level sample DataFrames from production files or move them into tests/examples.

## Code Organization and Deduplication

### Shared helper package

Affected areas: all packages  
Expected benefit: Smaller codebase and fewer divergent behaviors

Recommended shared modules:

- `common/pdf.py`
  - PDF path discovery
  - cached first-page/second-page text
  - reporting institution extraction
- `common/ui.py`
  - centered windows
  - processing modal
  - university dropdown
  - checklist dialogs
- `common/reports.py`
  - skipped-file report writer
  - output filename helpers
  - common error message behavior
- `common/excel.py`
  - currency format constants
  - border and fill helpers
  - average/median/rank formula helpers
- `common/sports.py`
  - sport normalization
  - men's-only and women's-only sport lists
  - sport aliases such as `XC/TF` and `Swimming and Diving`

### Replace wildcard imports

Priority: Medium  
Affected areas: most report modules  
Expected benefit: Clearer dependencies and fewer import side effects

Current pattern:

- Many modules use `from . import *`.
- Package `__init__.py` files import standard libraries, third-party libraries, Tkinter, and internal modules into a broad namespace.

Why it matters:

Wildcard imports hide where dependencies come from. They also make import order and circular import issues harder to debug. In this project, `__init__.py` imports many modules that then import from `__init__.py`, increasing the risk of circular behavior and slow startup.

Recommended fix:

- Replace `from . import *` with explicit imports in each file.
- Keep package `__init__.py` small.
- Export only the public workflow entrypoint, such as `run_ui`, when needed.
- Import heavy dependencies only where they are used.

### Consolidate report configurations

Priority: Medium  
Affected areas: Revenue, Sport Ops, Scholarship  
Expected benefit: Easier changes to NCAA table mappings and sport rules

Examples:

- Revenue table numbers and names are defined inside `rev/Folder_Parser.py`.
- Sport Ops table names are defined inside `sportops/Table_Extractor.py`.
- Men's-only and women's-only sport lists appear in multiple files.
- Sport normalization rules appear in multiple places.

Recommended fix:

- Move report table definitions into dedicated config constants.
- Keep aliases and output labels near those definitions.
- Reference the same sport gender lists from shared utilities.

## Report-Specific Notes

### Revenue and Ticket Sales

Priority: High  
Affected areas: `rev/Folder_Parser.py`, `rev/Testextract.py`, `rev/Data_Processing.py`, `rev/fill_excel_with_data_revenue.py`  
Expected benefit: Easier ticket/revenue optimization and fewer mapping mistakes

Current observations:

- Revenue extraction relies on configured table numbers such as `1` for `Ticket Sales`.
- Revenue columns are later combined in `combine_financial_columns(...)`.
- Revenue parsing and column-combination rules are embedded in general processing files.

Recommended improvements:

- Create a revenue table configuration that explicitly marks:
  - source table number
  - output column name
  - whether the column is combined with others
  - final display label
- Keep `Ticket Sales` as a first-class configured metric rather than just one entry in an inline dictionary.
- Add validation after parsing to show which expected revenue categories were found, missing, or combined.
- Add a small report summary for skipped or missing ticket sales data so users know whether zero means true zero or parse failure.

Complexity impact:

- Runtime complexity likely remains linear in PDF count and page count.
- Maintainability improves because revenue/ticket rules become data configuration rather than scattered code.

### Sport Ops

Priority: High  
Affected areas: `sportops/Table_Extractor.py`, `sportops/Folder_Parser.py`, `sportops/Data_Processing.py`  
Expected benefit: Faster table extraction and more reliable sport assignment

Recommended improvements:

- Cache page tables once per page.
- Use shared sport normalization and gender assignment helpers.
- Remove debug prints of entire extracted table dictionaries.
- Add clear skipped-file reasons when extraction returns `1`.
- Make fallback line parsing easier to test independently from PDF opening.

### Scholarship

Priority: Medium  
Affected areas: `scholar/extract_scholarships.py`, `scholar/ui.py`, `scholar/fill_excel_with_data_scholar.py`  
Expected benefit: Cleaner sport normalization and fewer duplicate sports

Current observations:

- Sport normalization is handled manually after collection.
- `Acrobatics and Tumbling` appears to be added to the male parsed list inside the female sport parsing branch.
- Debug prints output full male and female data dictionaries.

Recommended improvements:

- Use a single `clean_sport_name(...)` for both parsed data and unique sport lists.
- Move sport aliases into shared configuration.
- Remove full dictionary debug prints or convert them to optional logging.
- Use cached institution names from the initial PDF manifest.

### TOE

Priority: Medium  
Affected areas: `toe/data_extraction.py`, `toe/ui.py`  
Expected benefit: Faster TOE processing and cleaner Excel generation

Current observations:

- TOE extraction opens each PDF to search for total operating expenses.
- Institution extraction opens the same PDF again.
- Excel template generation and data fill logic live in the same file as PDF parsing.

Recommended improvements:

- Extract PDF parsing, workbook template generation, and workbook filling into separate modules.
- Reuse the shared institution-name cache.
- Precompile the TOE regex once.
- Keep skipped-file reporting consistent with other workflows.

### Launcher and UI

Priority: Medium  
Affected areas: `saui.py`, each package `ui.py`  
Expected benefit: Less repeated UI code and more consistent user experience

Current observations:

- The launcher correctly uses a child process for each workflow.
- Each workflow creates similar folder selection, progress modal, threading, save-file, and completion UI.
- Button state polling uses `after(200, check_process)`, which is reasonable.

Recommended improvements:

- Add a shared processing modal helper that runs a background task and calls a finalize callback on the Tkinter thread.
- Use consistent error handling when a background task fails.
- Avoid `sys.exit(...)` inside nested UI callbacks where possible; return status values and close windows cleanly.
- Remove unused imports such as `time` in `saui.py` if not needed.

## Packaging and Repository Hygiene

### Generated artifacts

Priority: High  
Affected areas: project root, `build/`, `dist/`, package `__pycache__/` directories, large release files  
Expected benefit: Smaller, cleaner, easier-to-share project

Recommended cleanup policy:

- Source tree should contain source, docs, config, and intentional fixtures only.
- Build outputs should be reproducible and generated outside the reviewed source tree.
- Release installers should live in a separate release archive location.

Suggested ignore patterns if Git is introduced:

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

If some spreadsheets in `testoutputs1/` are needed as test fixtures, move only those intentional files into a named `fixtures/` or `sample_outputs/` directory and document what each one validates.

### Project structure

Priority: Medium  
Affected areas: root package layout  
Expected benefit: Clearer boundaries between app source, generated output, and documentation

Suggested future layout:

```text
programlauncher/
  __main__.py
  saui.py
  common/
  rev/
  scholar/
  sportops/
  toe/
docs/
  PROJECT_REPORT.md
  OPTIMIZATION_AUDIT.md
releases/
  generated installers, not source-controlled
tests/
  fixtures/
```

This does not need to happen immediately, but it would make future handoff and packaging much cleaner.

## Suggested Refactor Roadmap

### Phase 1: Quick cleanup with low behavior risk

- Remove or gate debug `print(...)` calls behind a `verbose` flag.
- Move module-level sample DataFrames out of `rev/Data_Processing.py`.
- Replace unused imports and obvious wildcard imports in small files first.
- Add shared constants for currency number formats and sport gender lists.
- Add a source-focused `.gitignore` if the project is placed under Git.

### Phase 2: Shared utilities

- Create shared helpers for university-name extraction, PDF folder scanning, skipped-file reports, and common UI dialogs.
- Replace duplicate `getname.py`, `choose_uni.py`, `include_client.py`, `checklist.py`, and `write_report.py` usage with shared imports.
- Keep old files temporarily as compatibility wrappers if needed, then remove them after all workflows pass manual tests.

### Phase 3: Runtime optimization

- Build a per-workflow PDF manifest so institution names are extracted once.
- Pass cached PDF text into extraction functions where possible.
- Refactor Sport Ops table extraction so `page.find_tables()` is called once per page.
- Replace `iterrows()` in hot paths with `itertuples()` or vectorized operations.

### Phase 4: Report configuration and tests

- Move Revenue and Sport Ops table mappings into explicit config structures.
- Add validation summaries for expected categories such as `Ticket Sales`.
- Add lightweight tests for sport normalization, university-name extraction, revenue column combining, TOE regex extraction, and skipped-file reporting.
- Add sample PDFs or sanitized text fixtures if real PDFs cannot be committed.

## Quick Wins Checklist

- [ ] Create a shared `extract_reporting_institution(...)` and delete duplicate copies.
- [ ] Cache institution names during folder selection and reuse them during processing.
- [ ] Replace `from . import *` with explicit imports in frequently edited modules.
- [ ] Remove full-data debug prints from extraction loops.
- [ ] Move sample DataFrames out of production `Data_Processing.py` files.
- [ ] Replace `iterrows()` with `itertuples()` in Excel fill functions.
- [ ] Move repeated sport gender lists into shared constants.
- [ ] Move repeated sport normalization rules into one shared function.
- [ ] Add clear skipped-file reasons instead of only recording filenames.
- [ ] Keep `dist/`, `build/`, large installers, and `__pycache__/` out of the source folder.
- [ ] Add a `.gitignore` before placing this project under version control.
- [ ] Add small tests for Revenue/Ticket Sales parsing and column-combination rules.

