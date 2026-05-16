# Proposed Feature Implementation Details

## Purpose

This document expands the "Proposed Future Features" section from `IMPLEMENTATION_PLAN.md` into practical implementation notes. It is intended to help convert feature ideas into scoped engineering work after the optimization phases are complete.

The first six features are implemented in the current source tree. Later features still assume the shared utility work from the implementation plan is in place, especially:

- `common/pdf_manifest.py`
- `common/report_log.py`
- `common/dialogs.py`
- `common/sports.py`
- `common/run_summary.py`
- `common/progress.py`
- `common/settings.py`
- optional structured logging

## Feature Priority

### Near-Term User Value

1. Batch summary dashboard
2. Detailed skipped-file report
3. Preview before saving
4. Recent folders and default save location
5. Per-report progress details
6. Cancel processing

### Refactor and Validation Support

7. Configurable sport aliases
8. Revenue/Ticket Sales validation report
9. Built-in output comparison tool
10. Settings file expansion
11. Structured logging

### Advanced Workflow Expansion

12. Headless command-line mode
13. Report templates by client or conference
14. Automated update/version check
15. Input PDF quality checker

## Shared Foundation

Several proposed features use the same underlying run state object instead of each workflow inventing its own status format.

Suggested shared model:

```python
@dataclass
class WorkflowRunSummary:
    workflow: str
    folder_path: str
    output_path: str | None
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    pdfs_found: int
    processed_count: int
    skipped_count: int
    skipped_files: list[SkippedFileRecord]
    warnings: list[str]
    extra: dict[str, Any]
```

Suggested skipped-file model:

```python
@dataclass
class SkippedFileRecord:
    filename: str
    path: str
    institution_name: str | None
    workflow: str
    reason: str
    stage: str
    suggested_action: str | None = None
    exception_message: str | None = None
```

Suggested locations:

- `common/run_summary.py`
- `common/report_log.py`
- `common/settings.py`
- `common/progress.py`
- `common/pdf_quality.py`

Implemented locations:

- `common/run_summary.py`
- `common/report_log.py`
- `common/settings.py`
- `common/progress.py`
- `common/dialogs.py`
- `scholar/ui.py`
- `sportops/ui.py`
- `rev/ui.py`
- `toe/ui.py`
- workflow parser modules for summary/progress/cancel hooks

## 1. Batch Summary Dashboard

### Goal

Show a final window after report generation so users can quickly confirm what happened without reading terminal output or opening generated logs.

### Implementation Detail

Implemented through `WorkflowRunSummary` in `common/run_summary.py` and `show_summary(...)` in `common/dialogs.py`. Each workflow UI creates a summary before processing and passes it into the parser. The UI shows the summary after success, processing failure, skipped files, or cancellation.

The summary should include:

- workflow name
- number of PDFs found
- number processed successfully
- number skipped
- skipped-file reason counts
- output workbook path
- processing duration
- cancellation status

Not implemented yet:

- button to open the output folder

### Suggested Files

- `common/run_summary.py`
- `common/dialogs.py`
- `scholar/ui.py`
- `sportops/ui.py`
- `rev/ui.py`
- `toe/ui.py`

### Acceptance Criteria

- Implemented: a summary appears after each workflow completes, fails, or is cancelled.
- Implemented: the summary includes skipped-file reason counts.
- Implemented: the summary does not require terminal output to understand the run result.

## 2. Detailed Skipped-File Report

### Goal

Make skipped files actionable by explaining why each file failed and what the user should do next.

### Implementation Detail

Implemented by extending `common/report_log.py` to write structured CSV reports from `SkippedFileRecord`. Processing functions now add structured skipped records to the active `WorkflowRunSummary`.

Recommended reason codes:

- `not_pdf`
- `name_not_found`
- `no_extractable_text`
- `section_not_found`
- `table_not_found`
- `parse_error`
- `empty_result`
- `user_excluded`

Recommended stages:

- `folder_scan`
- `name_extraction`
- `quality_check`
- `section_detection`
- `table_extraction`
- `data_normalization`
- `workbook_write`

Suggested actions should be short and user-facing. Example: "Confirm this is an NCAA financial report PDF with selectable text."

Implemented reason/stage examples:

- Scholarship empty extraction uses `empty_result` at `scholarship_extraction`
- Sport Ops missing tables use `table_not_found` at `table_extraction`
- Revenue empty extraction uses `empty_result` at `revenue_extraction`
- Revenue exceptions use `parse_error` at `revenue_extraction`
- TOE missing section uses `section_not_found` at `toe_extraction`

### Suggested Files

- `common/report_log.py`
- `common/run_summary.py`
- all workflow parser modules

### Acceptance Criteria

- Implemented: skipped reports include one CSV row per skipped file.
- Implemented: each row includes reason and extraction stage.
- Implemented: old plain-string skipped items are still accepted for compatibility.

## 3. Preview Before Saving

### Goal

Let users catch wrong selections before generating a workbook.

### Implementation Detail

Implemented as a lightweight shared confirmation dialog in `common/dialogs.py`. After folder selection, manifest creation, and client selection, each workflow shows a preview before processing starts.

Preview contents by workflow:

- all workflows: selected client, include/exclude choice, peer institutions, PDF count
- Scholarship: detected sports and missing sport categories
- Sport Ops: detected sport categories and expected table availability if pre-scan is available
- Revenue: detected institutions and missing expected revenue sections if pre-scan is available
- TOE: institutions with detected TOE values if lightweight pre-scan is available

The current version intentionally stays lightweight. It uses manifest data and does not fully parse every workflow twice.

Implemented preview fields:

- workflow name
- selected client
- include/exclude client setting
- PDF count
- peer institution count
- first detected institutions, with an overflow count

### Suggested Files

- `common/dialogs.py`
- `common/pdf_manifest.py`
- workflow UI modules

### Acceptance Criteria

- Implemented: users can review detected institutions before processing starts.
- Implemented: users can cancel before processing starts.
- Implemented: preview uses manifest data and avoids expensive duplicate parsing.

## 4. Recent Folders and Default Save Location

### Goal

Reduce repeated folder selection for users who process the same NCAA folder often.

### Implementation Detail

Implemented in `common/settings.py`. Preferences are stored in a local user config directory, not in the repo or app bundle.

Example settings:

```json
{
  "last_pdf_folder": "/path/to/pdfs",
  "last_save_directory": "/path/to/output",
  "last_include_client": true,
  "recent_pdf_folders": []
}
```

When opening file dialogs, the app passes the last known folder as the initial directory. The app updates folder and save preferences when a user chooses a PDF folder or workbook output path. The launcher also remembers the include-client dropdown choice.

### Suggested Files

- `common/settings.py`
- workflow UI modules

### Acceptance Criteria

- Implemented: last selected PDF folder is remembered between app launches.
- Implemented: last save directory is remembered between app launches.
- Implemented: include-client preference is remembered from the launcher.
- Implemented: missing or moved folders are ignored gracefully.

## 5. Per-Report Progress Details

### Goal

Make long runs feel alive and give users better feedback during processing.

### Implementation Detail

Implemented with `ProgressReporter`, `ProgressSnapshot`, and `ProcessingDialog` in `common/progress.py`. Workflow parser loops update the current PDF count, institution, extraction stage, and skipped count.

Progress fields:

- current PDF index
- total PDF count
- current institution
- current extraction stage
- skipped count so far
- elapsed time, later enhancement

For Tkinter safety, the current threading approach is preserved. Worker threads publish progress snapshots to a queue, and the Tkinter dialog polls that queue with `after(...)`.

### Suggested Files

- `common/progress.py`
- `common/dialogs.py`
- workflow UI modules
- workflow parser modules

### Acceptance Criteria

- Implemented: progress text changes during processing.
- Implemented: current institution is visible.
- Implemented: skipped count is visible.
- Implemented: UI updates are routed through Tkinter-safe queue polling.

## 6. Cancel Processing

### Goal

Allow users to stop a mistaken or long-running job safely.

### Implementation Detail

Implemented with `CancellationToken` in `common/progress.py`. Each workflow parser checks the token between PDFs. The progress dialog includes a Cancel button that requests cancellation.

Expected behavior:

- user clicks Cancel
- current PDF finishes or reaches a safe stop point
- no incomplete workbook is written unless the user explicitly confirms
- summary dialog shows partial results and cancellation status

The cancellation token does not interrupt low-level PDF parsing mid-call. It stops at controlled checkpoints before the next PDF starts.

### Suggested Files

- `common/progress.py`
- `common/run_summary.py`
- workflow UI modules
- workflow parser modules

### Acceptance Criteria

- Implemented: Cancel button appears during long processing.
- Implemented: cancellation stops before the next PDF begins.
- Implemented: partial results are reported in the summary dialog.
- Implemented: no workbook is written after cancellation.

## 7. Configurable Sport Aliases

### Goal

Allow sport naming rules to be updated without editing Python source code.

### Implementation Detail

Implemented in `common/sports.py` and `common/settings.py`. Default sport aliases live in `DEFAULT_SPORT_ALIASES`, and user overrides are loaded from the `custom_sport_aliases` setting.

Example config:

```json
{
  "aliases": {
    "XC/TF": ["Track and Field", "Track and Field, X-Country"],
    "Swimming and Diving": ["Swimming and", "Swimming & Diving"],
    "Acrobatics and Tumbling": ["Acrobatics & Tumbling"]
  }
}
```

Implementation merges user aliases with defaults. Defaults remain available so a missing or invalid config does not break normalization. `SPORT_PATTERNS` is also built from default and configured aliases at app startup so Excel fill logic can benefit from aliases.

### Suggested Files

- `common/sports.py`
- `common/settings.py`
- optional `common/sport_aliases.json`

### Acceptance Criteria

- Implemented: default aliases continue to work.
- Implemented: user-defined aliases can extend defaults through settings.
- Implemented: invalid alias config falls back to defaults through settings validation.

## 8. Revenue/Ticket Sales Validation Report

### Goal

Make Revenue parsing quality more visible, especially for Ticket Sales.

### Implementation Detail

Implemented by having Revenue parsing produce extracted values and validation metadata. The metadata is stored on `summary.extra["revenue_validation"]` and written to a dedicated workbook sheet named `Validation` after the main Revenue sheet is filled.

Validation fields:

- institution name
- Ticket Sales found
- missing revenue categories
- categories combined into final metrics
- parse errors
- distinction between true zero and missing value

This should build on `rev/config.py` so table labels and combination rules are not duplicated.

Implemented validation statuses:

- `found_value`
- `found_zero`
- `missing`

### Suggested Files

- `rev/config.py`
- `rev/Folder_Parser.py`
- `rev/fill_excel_with_data_revenue.py`
- `common/report_log.py`

### Acceptance Criteria

- Implemented: Ticket Sales status is visible for every institution in the `Validation` sheet.
- Implemented: missing values are distinguishable from true zero values.
- Implemented: main Revenue workbook output remains isolated from validation metadata.

## 9. Built-In Output Comparison Tool

### Goal

Help developers compare baseline and refactored workbook outputs.

### Implementation Detail

Implemented as `scripts/compare_workbooks.py`, an admin/developer utility that loads two Excel workbooks and compares:

- sheet names
- row counts
- column counts
- cell values
- formulas
- missing institutions
- changed sport columns

This starts as a command-line script before being added to the UI. It uses `openpyxl` for workbook inspection.

Suggested command:

```bash
python scripts/compare_workbooks.py baseline.xlsx candidate.xlsx --output comparison_report.md
```

### Suggested Files

- `scripts/compare_workbooks.py`
- `tests/test_workbook_comparison.py`

### Acceptance Criteria

- Implemented: comparison report identifies changed sheets, formulas, values, and dimensions.
- Implemented: tool can be used without launching the Tkinter app.
- Implemented: known identical workbooks produce a clean comparison result.

## 10. Settings File

### Goal

Create a durable home for user preferences and future configurable behavior.

### Implementation Detail

Implemented a `SettingsStore` helper with:

- default values
- load
- save
- schema migration/version field
- validation and fallback for corrupt files

Suggested settings:

- default include-client setting
- default save folder
- verbose logging enabled or disabled
- custom sport aliases
- preferred output filename pattern
- recent folders
- log directory

Keep secrets out of this file. It should contain preferences only.

### Suggested Files

- `common/settings.py`
- tests for settings load/save behavior

### Acceptance Criteria

- Implemented: app creates settings on first use.
- Implemented: corrupt settings do not crash the app.
- Implemented: settings changes persist between app launches.
- Implemented: settings schema version and validation are centralized.

## 11. Structured Logging

### Goal

Make packaged desktop issues easier to diagnose.

### Implementation Detail

Implemented in `common/logging_config.py`. Each workflow starts a per-run log file, records run options, logs exceptions with tracebacks, and logs the final run summary.

Log contents:

- app version
- timestamp
- workflow
- selected folder
- selected client
- output path
- duration
- skipped-file records
- exceptions with tracebacks

Use Python's built-in `logging` module and configure file handlers in one place.

### Suggested Files

- `common/logging_config.py`
- `common/run_summary.py`
- workflow UI modules

### Acceptance Criteria

- Implemented: each run produces a log file in the configured log directory or default app support logs folder.
- Implemented: UI-level workflow exceptions are logged with tracebacks.
- Implemented: final summaries and skipped-file records are logged.

## 12. Automated Update/Version Check

### Goal

Let users confirm whether they are running the latest release.

### Implementation Detail

Add local version metadata first. A manual "Check for Updates" action can later compare the local version against a remote release source.

Recommended first step:

- centralize `__version__`
- show version in the launcher window
- add version to logs and release notes

Optional later step:

- fetch latest release metadata from GitHub
- compare semantic versions
- show a non-blocking dialog if an update exists

Network checks should be manual or opt-in to avoid unexpected delays in a desktop app.

### Suggested Files

- `programlauncher/__init__.py`
- `saui.py`
- `common/version.py`
- optional `common/update_check.py`

### Acceptance Criteria

- Current version is visible in the app.
- Version is included in logs.
- Manual update check handles offline mode gracefully.

## 13. Report Templates by Client or Conference

### Goal

Support reusable formatting and naming presets without editing Excel generator code.

### Implementation Detail

Create a template preset model that controls:

- title text
- conference name
- color palette
- included sports
- output filename pattern
- optional workbook metadata

Start with JSON presets and a default preset. Later, add UI selection in the launcher or workflow screens.

Example preset:

```json
{
  "name": "Default NCAA",
  "conference_name": "",
  "colors": {
    "title_fill": "1F4E78",
    "header_fill": "D9EAF7"
  },
  "output_filename": "{workflow}_{client}_{date}.xlsx"
}
```

### Suggested Files

- `common/templates.py`
- `common/excel_styles.py`
- workflow Excel generator modules

### Acceptance Criteria

- Default report appearance remains unchanged.
- A selected preset can change workbook title/colors/output name.
- Invalid preset data falls back to defaults.

## 14. Headless Command-Line Mode

### Goal

Enable repeatable processing without clicking through the UI.

### Implementation Detail

Add argparse support to `programlauncher/__main__.py` or a dedicated `cli.py`. UI launch should remain the default when no CLI arguments are provided.

Example command:

```bash
python -m programlauncher --report revenue --folder ./pdfs --client "Example University" --include-client yes --output ./revenue.xlsx
```

CLI should call the same processing functions as the UI. Avoid duplicating workflow logic. The CLI should print a concise run summary and return non-zero exit codes for failed runs.

### Suggested Files

- `programlauncher/__main__.py`
- `cli.py`
- `common/run_summary.py`
- workflow processing modules

### Acceptance Criteria

- Running `python -m programlauncher` still opens the UI.
- CLI mode can generate each report type.
- CLI mode returns useful exit codes and printed summaries.

## 15. Input PDF Quality Checker

### Goal

Warn users early about PDFs that are likely to fail extraction.

### Implementation Detail

Add a lightweight pre-check during manifest building or preview. Avoid full workflow parsing. The checker should inspect basic quality signals:

- file is a PDF
- file can be opened
- first pages contain extractable text
- reporting institution can be found
- expected NCAA section headings exist for the selected workflow

Quality results should feed into preview, skipped reports, and run summaries.

Suggested result model:

```python
@dataclass
class PdfQualityResult:
    path: str
    filename: str
    can_open: bool
    has_extractable_text: bool
    institution_name: str | None
    missing_signals: list[str]
    warnings: list[str]
```

### Suggested Files

- `common/pdf_quality.py`
- `common/pdf_manifest.py`
- `common/preview_dialog.py`

### Acceptance Criteria

- Scanned/image-only PDFs are flagged before processing.
- Wrong report types produce clear warnings when detectable.
- Quality checks do not significantly slow normal runs.

## Cross-Feature Implementation Sequence

1. Done: add `WorkflowRunSummary` and `SkippedFileRecord`.
2. Done: expand `common/report_log.py` to write detailed skipped records.
3. Done: add summary dashboard using the shared run summary.
4. Done: add settings persistence for recent folders and default save location.
5. Done: add preview dialog using PDF manifest data.
6. Done: add improved progress dialog and cancellation token.
7. Done: add configurable sport aliases.
8. Done: add Revenue/Ticket Sales validation output.
9. Done: add workbook comparison script.
10. Done: expand settings store for future configurable behavior.
11. Done: add structured logging using the same run summary.
12. Later: add CLI mode.
13. Later: add templates and update check after core reliability features are stable.
14. Later: add PDF quality checker and feed results into preview and skipped reports.

## Definition of Done

These proposed features are ready when:

- users can understand each run outcome without terminal output
- skipped and failed PDFs include actionable reasons
- repeated runs remember common choices
- long-running jobs show meaningful progress
- users can cancel before the next PDF begins
- Revenue/Ticket Sales missing data is visible
- settings, logs, and summaries are shared across all workflows
- new features reuse shared models instead of adding workflow-specific duplicates

Current implementation status:

- Features 1 through 11 are implemented across the shared utilities and relevant workflows.
- Tests cover run summaries, structured skipped reports, settings persistence, configurable sport aliases, Revenue validation sheets, structured logging, workbook comparison, sport normalization, and PDF filename fallback behavior.
- Features 12 through 15 remain proposed work.
