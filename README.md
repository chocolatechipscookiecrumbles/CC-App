# NCAA Report Tool

Desktop tool for generating NCAA financial report workbooks from NCAA FRS PDF folders.

The launcher supports four workflows:

- Scholarship reports
- Sport operating budget reports
- Revenue reports
- Total operating expenses reports

## Requirements

- Python 3.11 recommended
- Tkinter support for the selected Python install
- macOS or Windows for desktop use

Python dependencies are listed in `requirements.txt`:

```text
pandas
pdfplumber
openpyxl
pytest
pyinstaller
```

`tkinter` is part of the Python standard library, but some Python distributions install it separately.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Using `uv` is also supported:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

If you already use the local conda environment for this project:

```bash
conda activate toeapp
python -m pip install -r requirements.txt
```

## Run From Source

Run the launcher from the repository root:

```bash
python -m programlauncher
```

With conda, without activating the environment:

```bash
conda run -n toeapp python -m programlauncher
```

Direct launcher fallback:

```bash
python saui.py
```

## Settings

Use the **Settings** button in the top-right corner of the launcher to tune app preferences.

Settings are stored locally at:

```text
~/Library/Application Support/NCAA Report Tool/settings.json
```

On Windows, settings are stored under the user app data folder.

The settings page uses tabs:

- **Sport Aliases**: edit the system-wide sport normalization table, add alias groups, and delete selected rows with confirmation.
- **SportOps Tables**: edit the SportOps table number/name list and choose which rows are parsed and included in final SportOps workbooks.
- **Logs**: view the resolved logs folder, set a custom log folder, reset to the default log folder, and copy the logs path.

Sport aliases are comma-separated PDF phrases that normalize to a target sport name. For example, `TrackandField` and `Track and Field` can both normalize to `XC/TF`.

The default aliases appear as regular editable rows beside any rows you add. Adding, editing, or deleting rows updates the table immediately. Click **Save** to persist changes; the Settings window stays open so you can continue editing.

SportOps table choices default to the full NCAA table set used by the app. The built-in rows can be unchecked when you want to exclude them from output, but they cannot be deleted. Added rows can be edited or deleted, and **Reset to Defaults** restores the original built-in list. If the saved table settings are missing, invalid, or empty, the app falls back to the default SportOps table set.

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

Run tests from the repository root:

```bash
python -m pytest
```

For the local conda environment:

```bash
conda run -n toeapp python -m pytest
```

## Workbook Comparison

Compare two generated workbooks:

```bash
python scripts/compare_workbooks.py baseline.xlsx candidate.xlsx --output comparison_report.md
```

The comparison report checks sheet names, dimensions, formulas, and cell values.

## Build And Deploy

Build helpers are in `scripts/`:

- `scripts/build_macos.sh`
- `scripts/build_windows.ps1`

Build from the repository root after installing dependencies:

```bash
python -m PyInstaller __main__.spec
```

Or use the platform helper:

```bash
scripts/build_macos.sh
```

On Windows:

```powershell
.\scripts\build_windows.ps1
```

PyInstaller outputs generated app files under `build/` and `dist/`. These generated folders should stay out of Git.
