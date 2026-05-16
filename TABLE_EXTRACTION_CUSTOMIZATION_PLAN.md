# SportOps Table Customization Plan

## Summary

Add a Settings-driven way to customize which SportOps NCAA expense tables are parsed and included in final Excel report output. This feature lives on `feature/table-extraction-customization` and should be based on `main`.

This version intentionally focuses only on SportOps:

- Scholarship remains unchanged because it already uses detected sport checklists and a different selection model.
- Revenue remains unchanged because it has category merging and validation behavior that needs separate design.
- TOE remains unchanged because it currently extracts only one `Total Operating Expenses` value.

SportOps is the best first target because it already has a clear list of table numbers and table names used for parsing.

## Current State

### Settings

The app already has a tabbed Settings window in `common/settings_dialog.py` with:

- Sport Aliases
- Logs

Settings are persisted through `common/settings.py`.

### SportOps

SportOps currently defines table names and table numbers separately in `sportops/config.py`:

```python
SPORTOPS_TABLE_NAMES = [
    "21 Guarantees",
    "27 Recruiting",
    "28 Team Travel",
    "29 Sports Equipment, Uniforms and Supplies (no table header)",
    "30 Game Expenses",
    "31 Fund Raising, Marketing and Promotion",
    "35 Direct Overhead and Administrative Expenses",
    "36 Indirect Institutional Support",
    "37 Medical Expenses and Insurance",
    "38 Memberships and Dues",
    "39 Student-Athlete Meals (nontravel)",
    "40 Other Operating Expenses",
]

SPORTOPS_TABLE_NUMS = ["21", "27", "28", "29", "30", "31", "35", "36", "37", "38", "39", "40"]
```

This split should become one dictionary that is the source of truth for Settings labels, parser table matching, workbook headers, and tests. This dictionary is also the built-in default backup used whenever no saved user selection exists or settings cannot be loaded safely:

```python
SPORTOPS_TABLES = {
    "21": "Guarantees",
    "27": "Recruiting",
    "28": "Team Travel",
    "29": "Sports Equipment, Uniforms and Supplies",
    "30": "Game Expenses",
    "31": "Fund Raising, Marketing and Promotion",
    "35": "Direct Overhead and Administrative Expenses",
    "36": "Indirect Institutional Support",
    "37": "Medical Expenses and Insurance",
    "38": "Memberships and Dues",
    "39": "Student-Athlete Meals (nontravel)",
    "40": "Other Operating Expenses",
}
```

Compatibility helpers can still build the existing list forms:

```python
SPORTOPS_TABLE_NUMS = list(SPORTOPS_TABLES)
SPORTOPS_TABLE_NAMES = [f"{table_id} {label}" for table_id, label in SPORTOPS_TABLES.items()]
```

## Settings Design

Add a new Settings tab named `SportOps Tables`.

Persist the editable table dictionary and checked output rows in `settings.json`:

```json
{
  "sportops_tables": {
    "21": "Guarantees",
    "27": "Recruiting"
  },
  "sportops_output_tables": ["21", "27", "28", "29", "30", "31", "35", "36", "37", "38", "39", "40"]
}
```

Fallback behavior:

- If `sportops_tables` is missing or invalid, use the built-in default backup: every table in `SPORTOPS_TABLES`.
- If `sportops_output_tables` is missing or invalid, use every active table from the resolved table dictionary.
- If a saved list contains unknown table IDs, ignore those unknown IDs.
- If the saved list is empty, treat it as invalid for runtime report generation and fall back to the built-in default backup.
- If settings JSON is corrupt, keep existing settings fallback behavior and use the built-in default backup.

Settings UI behavior:

- Show an editable table with table number and table name columns plus a small checkbox for whether each row is included in parsing/output.
- Seed the table from the current built-in defaults when no saved table dictionary exists.
- Built-in default rows can be unchecked/deselected, but they cannot be deleted.
- Added/custom rows can be edited, unchecked, and deleted.
- Include `Reset to Defaults`, which restores the original built-in table numbers and names and checks every default row.
- Save persists choices and keeps Settings open.
- Cancel closes Settings and discards unsaved changes.
- If the user tries to Save with no SportOps tables selected, show a warning and offer to reset to defaults instead of saving an empty list.

## Shared Table Helpers

Add small helper functions rather than spreading table filtering logic across UI, parsing, and Excel generation.

Recommended functions:

```python
def clean_sportops_table_selection(value: object) -> list[str]:
    ...

def default_sportops_table_selection() -> list[str]:
    ...

def selected_sportops_tables() -> dict[str, str]:
    ...

def reset_sportops_output_tables() -> None:
    ...

def reset_sportops_tables() -> None:
    ...
```

Recommended location:

- `sportops/config.py` for `SPORTOPS_TABLES` and compatibility helpers.
- `common/settings.py` for loading/saving the selected IDs.

Avoid adding a broader cross-report abstraction in this first version. SportOps is the only workflow in scope.

## Workflow Behavior

SportOps should use the selected table IDs as the basis for extraction and final workbook output.

Behavior:

- Build the table title list from the active configured table dictionary before PDF parsing.
- If no valid saved selection exists, use the full built-in default backup.
- Initialize SportOps DataFrames with only selected table IDs.
- Ignore parsed tables whose ID is not selected.
- Per-sport sheets include selected expense category columns only.
- Men's Total and Women's Total sheets include selected expense category columns only.
- Total columns sum only visible selected columns.
- Header labels and column widths come from selected table metadata.
- If no SportOps tables are selected in the UI, prevent saving that empty selection unless the user resets to defaults.

Required code changes:

- Replace separate hardcoded table-name/table-number sources in `sportops/config.py` with `SPORTOPS_TABLES`.
- Update `sportops/Table_Extractor.py` to accept selected table names or table definitions.
- Update `sportops/Folder_Parser.py` to use selected table IDs from Settings.
- Replace hardcoded metric arrays in `sportops/Excel_Generator.py`.
- Pass selected table definitions into SportOps workbook builder/fill functions.
- Ensure `sportops/fill_excel_with_data_sportops.py` writes values by selected table ID order, not by hardcoded columns.

## Out Of Scope

- Scholarship output customization.
- Revenue output customization.
- TOE output customization.
- Per-run SportOps table prompts. This feature uses global Settings only.
- Changing SportOps sport selection checklists. Those remain separate from table/category selection.

## Implementation Steps

1. Convert SportOps table metadata to one `SPORTOPS_TABLES` dictionary.
2. Add SportOps table selection validation helpers.
3. Extend `DEFAULT_SETTINGS` with `sportops_tables` and `sportops_output_tables`.
4. Add `get_sportops_tables(...)`, `get_sportops_output_tables(...)`, and save/reset helpers.
5. Add `reset_sportops_tables(...)` to restore the built-in default backup.
6. Add the `SportOps Tables` Settings tab with an editable table, include checkboxes, protected default rows, custom-row deletion, and a `Reset to Defaults` button.
7. Make SportOps extraction use selected table IDs.
8. Make SportOps workbook generation use selected table IDs and labels.
9. Update README, `PROJECT_REPORT.md`, and `PROPOSED_FEATURE_IMPLEMENTATION.md`.
10. Add tests for settings fallback, validation, reset behavior, extraction filtering, Excel headers, and formulas.

## Test Plan

Run:

```bash
python -m pytest
conda run -n toeapp python -m pytest
```

Add or update tests for:

- Missing `sportops_output_tables` falls back to all SportOps tables.
- Missing `sportops_tables` falls back to the built-in default table dictionary.
- Empty saved selections fall back to all SportOps tables at runtime.
- Unknown table IDs are ignored.
- Reset helper restores all default SportOps tables.
- Built-in rows can be deselected but are not deleted.
- Custom rows can be added, edited, deselected, and deleted.
- Selected table names are generated from `SPORTOPS_TABLES`.
- SportOps parser ignores unselected table IDs.
- SportOps workbook headers reflect selected table IDs only.
- SportOps total formulas sum only visible selected columns.
- Settings prevents saving no selected SportOps table IDs, or prompts the user to reset to defaults.
- Scholarship, Revenue, and TOE tests continue passing without behavior changes.

## Acceptance Criteria

- Settings includes a `SportOps Tables` tab.
- Users can globally edit SportOps table definitions and select SportOps table categories.
- Selections are based on a dictionary of NCAA table numbers to table names plus checked output table IDs.
- Built-in default tables remain available as a backup, can be deselected, and cannot be deleted.
- Users can reset SportOps table settings to defaults from the Settings tab.
- Save persists choices; Cancel discards unsaved changes.
- SportOps extraction only targets selected table IDs.
- SportOps final workbooks only show selected table categories.
- SportOps total formulas use only selected visible columns.
- Scholarship, Revenue, and TOE behavior is unchanged.
- All tests pass in the normal Python environment and `toeapp`.

## Assumptions

- SportOps table choices are global defaults, not a new per-run prompt.
- The current full SportOps table list is the built-in default backup.
- SportOps sport checklists remain unchanged.
- Revenue customization is intentionally skipped because category merging needs separate design.
- Scholarship customization is intentionally skipped because it already uses a different detected-sport selection system.
- TOE customization is out of scope until TOE extraction supports individual category lines.
