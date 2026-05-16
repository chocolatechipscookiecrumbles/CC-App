# NCAA Report Tool Python Project Report

## Project Overview

This project is a desktop Python application that automates the creation of Excel reports from NCAA Financial Reporting System PDF files. The application is launched from a single Tkinter interface and supports four report workflows:

- Scholarship equivalency reports
- Sport operating budget reports
- Revenue reports
- Total operating expenses reports

The main purpose of the system is to reduce manual extraction from NCAA FRS PDF reports. Users select a folder of PDF files, choose a client university, optionally decide whether the client should be included in average and median calculations, and save a formatted Excel workbook generated from the extracted data.

## Main Technologies and Tools

### Python

Python is the main programming language used for the project. The code is organized into separate packages for each report type:

- `scholar/`
- `sportops/`
- `rev/`
- `toe/`

Each package contains its own user interface file, PDF extraction logic, data processing functions, Excel generation logic, and helper utilities.

### Tkinter

Tkinter is used to build the desktop graphical user interface. It provides:

- Main program launcher buttons
- A tabbed Settings window for sport aliases and logs
- Folder picker dialogs
- Save-file dialogs
- Message boxes
- Client university dropdowns
- Sport selection checklists
- Processing windows with progress details and cancellation

Important files:

- `saui.py`
- `common/settings_dialog.py`
- `common/progress.py`
- `scholar/ui.py`
- `sportops/ui.py`
- `rev/ui.py`
- `toe/ui.py`
- `choose_uni.py`
- `checklist.py`

### Multiprocessing

The launcher uses Python's `multiprocessing` module to run each report workflow in a separate process. This prevents one report window or long-running extraction job from blocking the main launcher.

Important implementation details:

- `multiprocessing.freeze_support()` is called in `__main__.py` and `saui.py` for packaged Windows compatibility.
- `multiprocessing.Process` is used in `saui.py`.
- The launcher disables report buttons while a child process is running, then re-enables them after the process exits.

### Threading

Individual report modules use `threading.Thread` to run PDF parsing in the background while the Tkinter progress window remains responsive. Tkinter updates are returned to the main GUI thread with `root.after(...)`.

The current processing dialog shows PDF count, current institution, extraction stage, skipped count, and a cancel button. Cancellation is cooperative and stops at safe checkpoints between PDFs.

This technique is used in:

- `scholar/ui.py`
- `sportops/ui.py`
- `rev/ui.py`
- `toe/ui.py`

### pdfplumber

`pdfplumber` is used to read PDF text and tables. It is central to the project because the source data comes from NCAA FRS PDF documents.

The project uses `pdfplumber` for:

- Extracting first-page and second-page text for university names
- Reading scholarship sections line by line
- Searching for total operating expenses with regular expressions
- Reading revenue summary text
- Extracting sport operating budget tables
- Falling back from table extraction to text-line parsing when needed

Important files:

- `scholar/extract_scholarships.py`
- `sportops/Table_Extractor.py`
- `rev/Testextract.py`
- `toe/data_extraction.py`
- `getname.py` files in each package

### pandas

`pandas` is used for tabular data cleaning, aggregation, sorting, reshaping, and preparation before writing to Excel.

Examples of pandas usage:

- Creating DataFrames from dictionaries of extracted PDF values
- Sorting universities alphabetically
- Creating male and female scholarship DataFrames
- Building sport-specific DataFrames
- Combining revenue columns
- Filling missing values with zero
- Converting parsed values to numeric form
- Creating men's and women's total sport summaries

Important files:

- `scholar/extract_scholarships.py`
- `sportops/Data_Processing.py`
- `sportops/Folder_Parser.py`
- `rev/Data_Processing.py`
- `rev/Folder_Parser.py`
- `toe/data_extraction.py`

### openpyxl

`openpyxl` is used to create, format, and populate Excel workbooks.

The project uses `openpyxl` for:

- Creating workbooks and worksheets
- Adding merged title cells
- Writing report headers
- Applying fills, fonts, alignment, borders, and number formats
- Creating formulas for totals, averages, medians, and ranks
- Creating multiple report sheets dynamically
- Handling merged cells safely when writing values

Important files:

- `scholar/build_scholarship_sheet.py`
- `scholar/fill_excel_with_data_scholar.py`
- `sportops/Excel_Generator.py`
- `sportops/fill_excel_with_data_sportops.py`
- `rev/Excel_Generator.py`
- `rev/fill_excel_with_data_revenue.py`
- `toe/data_extraction.py`

### PyInstaller

The project includes a PyInstaller spec file, `__main__.spec`, used to package the Python application into a desktop application.

Packaging settings include:

- Entry script: `__main__.py`
- Windowed mode: `console=False`
- UPX compression: `upx=True`
- macOS app bundle generation through `BUNDLE`
- Collected output under `dist/` and build metadata under `build/`

### Shared Utilities

The project now includes shared utilities under `common/` for cross-workflow behavior:

- `pdf_names.py` and `pdf_manifest.py` centralize PDF name extraction and folder scanning.
- `dialogs.py`, `progress.py`, and `run_summary.py` support preview dialogs, progress windows, cancellation, and final batch summaries.
- `report_log.py` writes structured skipped-file CSVs.
- `settings.py` and `settings_dialog.py` manage persistent settings and the tabbed Settings UI.
- `sports.py` centralizes sport aliases, sport patterns, and gender-list constants.
- `logging_config.py` writes per-run logs.

## High-Level Project Flow

1. The application starts from `__main__.py`.
2. `__main__.py` prepares import paths and calls `create_launcher_ui()` from `saui.py`.
3. The launcher displays four report buttons:
   - Scholar
   - Sport Ops
   - Revenue
   - TOE
4. The user chooses whether to include the client university in mean and median calculations.
5. The user may open Settings to configure sport aliases or the log location.
6. When the user clicks a report button, the launcher starts that workflow in a separate process.
7. The selected workflow asks the user to choose a folder containing NCAA FRS PDF files.
8. The workflow builds a PDF manifest and detected institution list.
9. The user selects the client university from a dropdown.
10. A preview dialog summarizes the workflow, selected client, include/exclude setting, PDF count, and detected institutions.
11. PDF parsing runs in a background thread while a detailed progress dialog is shown.
12. The user chooses output sports or report options if the workflow requires it.
13. The user chooses where to save the Excel workbook.
14. The project generates a styled Excel template.
15. Extracted and processed data is written into the workbook.
16. The program shows a batch summary with processed/skipped counts, output path, duration, and log path.

## Entry Point and Launcher Design

### `__main__.py`

`__main__.py` is the application entry point. It supports running the project with:

```bash
python -m programlauncher
```

Key techniques:

- Inserts the parent directory into `sys.path` so package imports work.
- Calls `multiprocessing.freeze_support()` for packaged executable compatibility.
- Imports the launcher only inside `main()` to reduce startup and packaging issues.

### `saui.py`

`saui.py` builds the main launcher window.

Main functions:

- `create_launcher_ui()`
- `launch_program(...)`
- `run_scholar(...)`
- `run_revenue(...)`
- `run_sportops(...)`
- `run_toe(...)`

Techniques used:

- A Tkinter root window displays report buttons.
- A top-right Settings button opens the tabbed Settings window.
- A `ttk.Combobox` captures whether the client should be included in mean and median calculations.
- Each report button maps to a wrapper function through `program_map`.
- The selected report runs in a separate child process.
- Buttons and dropdowns are disabled while a report process is active.
- `after(200, check_process)` polls the process without blocking the UI.

### Settings Window

`common/settings_dialog.py` implements a tabbed Settings window.

The Sport Aliases tab:

- Shows instructions and an example for comma-separated aliases.
- Displays an authoritative two-column table with normalized sport names and PDF phrases.
- Shows default and saved alias groups as regular editable rows.
- Lets users add alias groups to the table before saving.
- Lets users select a row and delete it with a warning.
- Saves changes without closing the Settings window.

The Logs tab:

- Shows the resolved logs folder.
- Lets users set a custom log directory.
- Lets users reset to the default logs directory.
- Lets users copy the logs path.
- Explains that skipped CSVs are stored separately in the selected PDF folder.

## Shared User Interface Methods

Each report workflow follows a similar UI pattern:

- Hide the root Tkinter window with `root.withdraw()`.
- Use `messagebox.showinfo(...)` to instruct the user.
- Use `filedialog.askdirectory(...)` to choose the PDF folder.
- Build a PDF manifest and university list from the selected folder.
- Use `choose_university(...)` to select the client.
- Show a preview confirmation dialog.
- Show a modal processing window with detailed progress and cancellation.
- Run parsing work in a background thread.
- Use `filedialog.asksaveasfilename(...)` to select the output Excel file.
- Generate the workbook and write data.
- Show a final batch summary.

The client selector is implemented in each package's `choose_uni.py`. It creates a topmost `Toplevel` window with a readonly `ttk.Combobox`.

The sport checklist is implemented in each package's `checklist.py`. It lets users confirm which detected sports should appear in the report.

## University Name Extraction

University-name extraction is centralized in `common/pdf_names.py`; package `getname.py` files remain as compatibility wrappers where needed.

Method used:

1. Open the PDF with `pdfplumber`.
2. Read the first and second page text.
3. Normalize whitespace with regular expressions.
4. Search for a `Reporting Institution` field.
5. Stop the match before nearby metadata fields such as reporting year, fiscal year, academic year, report date, or report period.
6. Fall back to line-based matching if the primary regex fails.
7. Insert spaces into camel-cased names such as `UtahStateUniversity`.
8. Return `None` if no institution name can be found.

If extraction fails, the workflow falls back to the PDF filename and removes suffixes such as `, FY24`.

## Scholarship Report Workflow

Main files:

- `scholar/ui.py`
- `scholar/extract_scholarships.py`
- `scholar/build_scholarship_sheet.py`
- `scholar/fill_excel_with_data_scholar.py`

### Input

The user selects a folder of NCAA FRS PDF files. The workflow searches the PDFs for scholarship equivalency data.

### Extraction Method

`extract_scholarships(pdf_path)` reads each PDF page with `pdfplumber` and tracks which section is currently being parsed:

- Male Athlete Scholarships
- Female Athlete Scholarships
- Not Allocated by Gender Scholarships

Techniques used:

- Section-state parsing with a `section` variable.
- Line-by-line PDF text processing.
- Regular expressions to detect section headers.
- A `buffer_line` to merge sport names split across multiple PDF lines.
- Filtering of non-data lines containing text such as `NCAA`, `Page`, `Report`, `System`, `AthleticAid`, `Equivalencies`, `Receiving`, `Medical`, and `Totals`.
- Regex matching of sport name plus numeric equivalency:

```text
sport name + numeric value
```

Extracted values are stored in two dictionaries:

- `male_data`
- `female_data`

### Folder Processing

`process_folder(folder_path, exclude_words, manifest=...)` loops through PDF records from the shared manifest.

Methods used:

- Skips non-PDF files.
- Reuses the university name from the manifest.
- Extracts male and female scholarship data.
- Filters out excluded words such as `NCAA`, `Other`, `Expenses`, and `Total`.
- Tracks unread or empty files.
- Builds a complete set of detected male and female sports.
- Normalizes known and configured sport variants:
  - Track and field/cross country becomes `XC/TF`
  - Swimming variants become `Swimming and Diving`
  - Acrobatics variants become `Acrobatics and Tumbling`
- Allows user-defined alias phrases through the Settings window.
- Creates sorted pandas DataFrames for male and female scholarship data.
- Writes a structured skipped-file CSV when files could not be read.

### Excel Generation

`generate_template_excel_scholar(...)` creates a workbook with two sheets:

- `Men's Sports`
- `Women's Sports`

`build_scholarship_sheet(...)` creates the structure for each sheet.

Excel techniques used:

- Merged title row
- Black title fill with white bold text
- Orange header row
- Gray client row
- Thin and medium borders
- Center and right alignment
- Dynamically sized sport columns
- Total column using Excel `SUM`
- Average row using `AVERAGE`
- Median row using `MEDIAN`
- Rank row using `RANK`
- Optional inclusion or exclusion of the client row in average and median formulas

### Writing Data

`fill_excel_with_data_scholar(...)` opens the template and writes extracted values.

Methods used:

- Creates header-to-column mappings from row 3.
- Uses regex sport patterns to match extracted sport names to workbook headers.
- Falls back to normalized sport-name matching for unexpected header variants.
- Writes the client university to row 4.
- Writes comparison universities starting at row 5.
- Uses `safe_write(...)` to handle merged cells and blank values.
- Applies black fill to blank, zero, or missing data.

## Sport Operating Budget Report Workflow

Main files:

- `sportops/ui.py`
- `sportops/Table_Extractor.py`
- `sportops/Folder_Parser.py`
- `sportops/Data_Processing.py`
- `sportops/Excel_Generator.py`
- `sportops/fill_excel_with_data_sportops.py`

### Input

The user selects NCAA FRS PDFs and chooses a client university. The workflow extracts sport-level operating budget data from expense tables.

### Target Tables

The sport operating budget workflow targets NCAA table numbers:

- `21` Guarantees
- `27` Recruiting
- `28` Team Travel
- `29` Sports Equipment, Uniforms and Supplies
- `30` Game Expenses
- `31` Fund Raising, Marketing and Promotion
- `35` Direct Overhead and Administrative Expenses
- `36` Indirect Institutional Support
- `37` Medical Expenses and Insurance
- `38` Memberships and Dues
- `39` Student-Athlete Meals
- `40` Other Operating Expenses

These become the report metrics:

- Guarantees
- Recruiting
- Travel
- Equipment
- Game
- Fundraising/Marketing
- Admin
- Indirect Institutional Support
- Medical
- Membership
- S-A Meals
- Other

### Table Extraction Method

`extract_tables_by_title(pdf_path)` uses two extraction approaches.

Primary approach:

- Use `page.find_tables()` from `pdfplumber`.
- Extract table rows structurally.
- Detect tables whose header matches `Expenses by Object of Expenditure`.
- Convert extracted table rows into a pandas DataFrame.

Fallback approach:

- Split PDF text into lines.
- Detect target table titles with regex.
- Search nearby lines for a table header.
- Parse rows manually with regex.
- Extract category, men amount, women amount, and not-allocated amount.

Techniques used:

- Flexible title matching for table numbers and names.
- Whitespace-insensitive header matching with `_squish(...)`.
- Regex row parsing for positive, negative, comma-formatted, and decimal numbers.
- Heuristic stop conditions for page footers, unrelated sections, and long spans without numbers.
- Gender keyword detection for one-value rows.
- Exclusion of total rows and non-team expenses before returning data.

### Gender Detection and Sport Normalization

The project uses keyword lists to identify single-gender sports:

Men's-only examples:

- Football
- Baseball
- Rifle
- Crew

Women's-only examples:

- Softball
- Beach Volleyball
- Field Hockey
- Bowling
- Equestrian
- Rugby
- Rowing in some extraction contexts

Shared sports are split into separate `Men's Sport` and `Women's Sport` report entries.

Sport normalization handles:

- Whitespace cleanup
- Ampersand replacement
- Parenthetical gender marker removal
- Stray punctuation removal
- Soccer variants
- Track/cross country variants as `XC/TF`
- Acrobatics and tumbling variants

### Misattribution Correction

`fix_misattributions_coeffs(...)` handles cases where PDF extraction places values in the wrong gender column.

Method used:

1. Treat the last row as a reported total row.
2. Compare summed body rows against reported men and women totals.
3. Calculate the overage in the left column and shortage in the right column.
4. If the overage and shortage balance, search for rows that should move from men to women.
5. Use exact subset-sum dynamic programming when values are integer-like.
6. Move full row amounts from one gender column to the other when a matching subset is found.
7. Handle negative candidate rows by adjusting the subset target.
8. Include special rifle handling because rifle may appear in either gender allocation depending on the source PDF.

This is one of the more advanced techniques in the project because it uses an algorithmic correction step instead of only direct parsing.

### Folder Aggregation

`collect_sports_across_pdfs(folder_path, manifest=...)` loops over manifest records and builds a dictionary of DataFrames.

Returned structure:

```text
{
  sport_name: DataFrame(
    rows = universities,
    columns = table numbers,
    values = extracted dollar amounts
  )
}
```

The function also returns:

- A set of detected men's sports
- A set of detected women's sports

Unread PDFs are written to a timestamped skipped-file CSV.

### Excel Generation

`generate_template_excel_totalsports(...)` creates the workbook. Individual sheets are created later based on detected sports.

`build_totalsports_sheet(...)` creates a sport-specific operating budget sheet with:

- Institution column
- Expense category columns
- Total operating expenses column
- Client row
- Average, median, and rank rows
- Excel formulas for totals and statistics
- Currency number formatting
- Styled borders and fills

`build_total_sports_total_sheet(...)` creates summary sheets:

- `Men's Total`
- `Women's Total`

These sheets summarize total sport operating budgets across selected sports.

### Writing Data

`fill_excel_with_data_sportops(...)`:

- Filters extracted sports against the user's checklist selections.
- Creates one worksheet per included sport.
- Writes the client row separately.
- Writes comparison schools below the client row.
- Applies black fill to zero, blank, or missing values.
- Generates men's and women's total summary DataFrames.
- Writes summary sheets using regex-based sport header matching.

## Revenue Report Workflow

Main files:

- `rev/ui.py`
- `rev/Testextract.py`
- `rev/Folder_Parser.py`
- `rev/Data_Processing.py`
- `rev/Excel_Generator.py`
- `rev/fill_excel_with_data_revenue.py`

### Input

The user selects a folder of NCAA FRS PDFs and chooses a client university. The workflow extracts total revenue values by category.

### Target Revenue Categories

The revenue parser targets these NCAA category IDs:

- `1` Ticket Sales
- `2` Direct State or Other
- `3` Student Fees
- `4` Direct Institutional
- `7` Guarantees
- `8` Contributions
- `11` Media Rights
- `12` NCAA Distributions
- `13` Conference Distributions
- `13A` Conference Distributions of Football Bowl Generated Revenue
- `14` Program, Novelty, Parking and Concession Sales
- `15` Royalties, Licensing, Advertisement and Sponsorships
- `18` Other Operating
- `19` Football Bowl

### Extraction Method

`extract_summary_totals(pdf_path)` reads all PDF pages into text and extracts a revenue summary block.

Techniques used:

- Normalize spaces, tabs, and nonbreaking spaces.
- Locate the `Revenue / Expense Summary` section.
- Stop before the Athletic Student Aid section when possible.
- Use regex to find optional category ID, category label, and dollar value.
- Prefer direct category ID matching when available.
- Fall back to name-overlap matching against known revenue labels.
- Convert comma-formatted dollar values to integers.

### Folder Aggregation

`collect_revenue_across_pdfs(folder_path, manifest=...)`:

- Loops through all PDFs in the selected folder.
- Reuses reporting institution names from the manifest.
- Calls `extract_summary_totals(...)`.
- Skips unreadable files.
- Creates a pandas DataFrame with universities as the index.
- Sorts rows alphabetically.
- Writes a structured skipped-file CSV for skipped PDFs.
- Records validation metadata for Ticket Sales and missing revenue categories.

### Data Processing

`combine_financial_columns(df)` combines related NCAA revenue categories before report output:

- `2` combines category `2` and `4`
- `12` combines category `12` and `13`
- `16` combines category `13A` and `19`

The generated report labels these combined values as broader report categories such as institutional/government support, NCAA/conference, and conference/bowl.

### Excel Generation

`generate_template_excel_revenue(output_path)` creates a workbook.

`build_total_revenue_sheet(...)` builds the formatted revenue report sheet.

Metrics used in the workbook:

- Ticket Sales
- Institutional/Government Support
- Student Fees
- Guarantees
- Contributions
- Media Rights
- NCAA/Conference
- Program, Novelty, Parking and Concession Sales
- Corporate Sponsorship
- Conference/Bowl
- Other

The sheet includes:

- Client row
- Comparison university rows
- Total column
- Average row
- Median row
- Rank row
- Currency formatting
- Black fills for unavailable values
- Optional inclusion of client in average and median formulas

The Revenue workflow also writes a `Validation` sheet containing Ticket Sales status, Ticket Sales value when found, missing/found revenue categories, combination rules, skipped status, and parse errors.

## Total Operating Expenses Report Workflow

Main files:

- `toe/ui.py`
- `toe/data_extraction.py`

### Input

The user selects NCAA FRS PDFs and chooses a client university. The workflow extracts the total operating expenses amount from each PDF.

### Extraction Method

`extract_total_operating_expensesregx(pdf_path)` uses `pdfplumber` and a regular expression to find:

```text
Total Operating Expenses $value Total of Categories 20-41A
```

The captured dollar value is converted from comma-formatted text to an integer.

### Folder Processing

`parse_folder_toe(folder_path, client_uni)`:

- Loops through PDFs in the folder.
- Extracts the total operating expenses value.
- Extracts or falls back to the university name.
- Separates the client value from comparison universities.
- Builds a pandas DataFrame with columns `University` and `TOE`.
- Sorts universities alphabetically.
- Writes a skipped-file report for PDFs that could not be parsed.

### Excel Generation and Writing

`generate_template_excel(output_path, num_items, ifclient)` creates a single-sheet workbook named `Total Operating Expenses`.

The sheet contains:

- Report title: `CONFERENCE - Total Athletic Budget`
- Institution column
- Budget column
- Client row
- Comparison rows
- Average row
- Median row
- Rank row

`fill_excel_with_data(...)` writes:

- Comparison university names and budgets
- Client university and client budget
- Currency formatting for budget cells

## Excel Formula Strategy

The project writes formulas directly into Excel rather than calculating all statistics in Python. This gives the final workbook live formulas that update if a user edits values.

Common formulas:

```excel
=SUM(C4:N4)
=AVERAGE(C4:C12)
=MEDIAN(C4:C12)
=RANK(C4,C4:C12)
```

When the user chooses not to include the client in mean and median calculations, formulas start from row 5 instead of row 4:

```excel
=AVERAGE(C5:C12)
=MEDIAN(C5:C12)
```

The rank formula still ranks the client value against the comparison range.

## Missing and Zero Value Handling

The project uses `safe_write(...)` helper functions in report writers.

This method:

- Checks if the target cell is part of a merged range.
- Writes to the top-left cell of the merged range when necessary.
- Treats `None`, `0`, `NaN`, and blank strings as unavailable data.
- Writes an empty string for unavailable values.
- Applies a black fill to visually mark missing or zero cells.

This keeps generated workbooks clean and clearly identifies unavailable data points.

## Error and Skip Reporting

Each report workflow records files that cannot be parsed successfully and produces a structured skipped-file CSV only when files are skipped.

Method:

- Maintain structured skipped-file records with workflow, filename, institution name, reason, extraction stage, suggested action, optional exception message, and path.
- After processing, call `write_report(folder_path, items)`.
- Create a timestamped `skipped_<workflow>_<timestamp>.csv` report inside the selected PDF folder.
- Omit skipped CSV output when no files were skipped.

This supports auditability because users can see which PDFs were excluded from the final Excel output.

Per-run logs are separate from skipped CSVs. Logs are written to the configured logs folder, defaulting to:

```text
~/Library/Application Support/NCAA Report Tool/logs
```

The final batch summary displays the log path for the run.

## Data Cleaning and Normalization Methods

The project relies heavily on regular expressions and normalization because PDF extraction often produces inconsistent text.

Cleaning techniques include:

- Collapsing multiple spaces into one
- Removing nonbreaking spaces
- Removing filename year suffixes such as `, FY24`
- Converting ampersands to `and`
- Removing trailing punctuation
- Removing parenthetical gender markers
- Adding spaces inside camel-cased institution names
- Converting comma-formatted numbers to integers
- Mapping sport aliases into standard labels
- Applying the system-wide sport alias table from Settings
- Filtering rows with words like `expenses`, `team`, `total`, and `other`

## Report Styling Methods

All reports are designed to look like consulting deliverables rather than raw data exports.

Styling methods include:

- Black merged title rows with white bold text
- Orange section headers
- Gray client rows
- Medium borders around report sections
- Thin borders inside data grids
- Center alignment for numeric values
- Right alignment for summary labels
- Currency number formats for financial reports
- Wider institution columns for readability
- Dynamically generated sport columns based on actual extracted data

## Project Structure

```text
programlauncher/
  __main__.py
  saui.py
  __main__.spec
  common/
    dialogs.py
    logging_config.py
    pdf_manifest.py
    pdf_names.py
    progress.py
    report_log.py
    run_summary.py
    settings.py
    settings_dialog.py
    sports.py
  scholar/
    ui.py
    extract_scholarships.py
    build_scholarship_sheet.py
    fill_excel_with_data_scholar.py
    choose_uni.py
    checklist.py
    getname.py
    write_report.py
  sportops/
    ui.py
    Table_Extractor.py
    Folder_Parser.py
    Data_Processing.py
    Excel_Generator.py
    fill_excel_with_data_sportops.py
    choose_uni.py
    checklist.py
    getname.py
    write_report.py
  rev/
    ui.py
    Testextract.py
    Folder_Parser.py
    Data_Processing.py
    Excel_Generator.py
    fill_excel_with_data_revenue.py
    choose_uni.py
    getname.py
    write_report.py
  toe/
    ui.py
    data_extraction.py
    choose_uni.py
    getname.py
    write_report.py
```

Generated packaging and output folders are also present:

- `build/`
- `dist/`
- `testoutputs1/`

These are not core source modules, but they show that the application has been packaged and test Excel outputs have been generated.

## Important Implementation Details

### Client Row Placement

The client university is always placed in row 4. Comparison universities begin at row 5. This makes formulas and formatting consistent across report types.

### Include Client Option

The launcher asks:

```text
Include client in mean / median?
```

The result is passed into the selected workflow as `include_client`.

If `include_client` is true, average and median formulas include row 4. If false, they start at row 5.

### Dynamic Workbook Shape

The workbook structure is not fixed. It changes based on:

- Number of PDFs parsed
- Sports found in the PDFs
- Sports selected by the user
- Report type
- Client inclusion setting

The code calculates final data rows and summary rows with:

```python
start_row = 5
end_row = start_row + num_items - 1
avg_row = end_row + 1
median_row = end_row + 2
rank_row = end_row + 3
```

### PDF Extraction Fallbacks

The project uses fallback strategies because PDF formatting varies by institution:

- If university name extraction fails, use the filename.
- If structured table extraction fails, use regex line parsing.
- If category IDs are missing in revenue extraction, match by category name overlap.
- If sport names are split across lines, buffer and merge them.
- If rows have only one amount, infer gender using sport keywords.

## Strengths of the Project

- Automates repetitive manual PDF-to-Excel work.
- Handles four related NCAA report types from one launcher.
- Uses separate modules for extraction, processing, UI, and Excel writing.
- Uses pandas for structured data management.
- Uses openpyxl for professional Excel formatting and formulas.
- Includes fallback parsing strategies for inconsistent PDF layouts.
- Includes algorithmic correction for gender-column misattribution in sport operating budgets.
- Produces structured skipped-file CSVs and per-run logs.
- Provides preview, progress, cancellation, and final batch summaries.
- Supports configurable sport aliases from the launcher Settings window.
- Adds Revenue/Ticket Sales validation output.
- Includes automated tests for shared parsing, settings, logging, validation sheets, and workbook comparison helpers.
- Supports packaging as a desktop app with PyInstaller.

## Limitations and Considerations

- PDF parsing depends on consistent enough NCAA FRS text extraction.
- Many extraction rules are regex-based, so unusual PDF layouts may still fail.
- Some package-level helper files remain as compatibility wrappers, although key behavior has been centralized in `common/`.
- Some debug `print(...)` statements remain in processing modules.
- Dependency versions are not pinned in a requirements file in the project root.
- Packaged build artifacts are stored in the same tree as source files, which can make navigation harder.

## Possible Future Improvements

- Add a `requirements.txt` or `pyproject.toml` with pinned dependencies.
- Add sample PDFs or mocked text fixtures for repeatable testing.
- Continue consolidating remaining compatibility wrappers into shared utilities.
- Replace remaining debug prints with structured logging.
- Add deeper PDF quality checks before processing.
- Add command-line report generation for automated runs.
- Add report template presets by client or conference.
- Exclude generated `build/`, `dist/`, and `__pycache__/` files from source control.

## Summary

This Python project is a practical desktop automation tool for generating NCAA financial comparison reports. It combines Tkinter for user interaction, pdfplumber for PDF extraction, pandas for data organization, openpyxl for Excel report generation, and PyInstaller for desktop packaging. The project's main technical work is in robust PDF parsing, sport and category normalization, dynamic Excel template generation, statistical formula construction, configurable user settings, structured run reporting, and user-guided report customization.
