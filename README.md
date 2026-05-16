# NCAA Report Tool

Desktop tool for generating NCAA report workbooks from FRS PDF folders.

The launcher supports four workflows:

- Scholarship reports
- Sport operating budget reports
- Revenue reports
- Total operating expenses reports

## Run From Source

Recommended environment:

```bash
conda activate toeapp
python -m programlauncher
```

Without activating the environment:

```bash
conda run -n toeapp python -m programlauncher
```

Direct launcher fallback:

```bash
python saui.py
```

## Feature Branch

Current feature work lives on:

```bash
feature/proposed-features-1-6
```

This branch includes workflow improvements from the proposed feature plan, including:

- input preview before processing
- detailed progress with cancellation
- final batch summary
- structured skipped-file CSVs
- remembered folders and save locations
- configurable sport aliases in the launcher Settings window
- per-run logs
- Revenue/Ticket Sales validation sheet
- workbook comparison script

## Settings

Use the **Settings** button in the top-right corner of the launcher to tune sport alias phrases.

Settings are stored locally at:

```text
~/Library/Application Support/NCAA Report Tool/settings.json
```

The settings page currently supports:

- custom sport alias phrases
- custom log folder path

Custom aliases are comma-separated phrases that normalize to a target sport name. For example, `TrackandField` and `Track and Field` can both normalize to `XC/TF`.

## Logs And Skipped Reports

Per-run logs are stored by default at:

```text
~/Library/Application Support/NCAA Report Tool/logs
```

The final batch summary also displays the log path for the run.

Skipped-file CSVs are written into the selected PDF folder only when files are skipped. File names follow this pattern:

```text
skipped_scholar_YYYYMMDD_HHMMSS.csv
skipped_sportops_YYYYMMDD_HHMMSS.csv
skipped_revenue_YYYYMMDD_HHMMSS.csv
skipped_toe_YYYYMMDD_HHMMSS.csv
```

Each skipped CSV includes workflow, filename, institution name, reason, extraction stage, suggested action, exception message, and path.

## Tests

Run tests in the project environment:

```bash
conda run -n toeapp python -m pytest
```

The lightweight local test run is:

```bash
python -m pytest
```

Some tests may skip outside `toeapp` if full PDF dependencies are not installed.

## Workbook Comparison

Compare two generated workbooks:

```bash
python scripts/compare_workbooks.py baseline.xlsx candidate.xlsx --output comparison_report.md
```

The comparison report checks sheet names, dimensions, formulas, and cell values.

## Build Scripts

Build helpers are in `scripts/`:

- `scripts/build_macos.sh`
- `scripts/build_windows.ps1`

Generated build/release outputs should stay out of Git. The repo ignores common generated folders such as `build/`, `dist/`, `__pycache__/`, and local test output folders.
