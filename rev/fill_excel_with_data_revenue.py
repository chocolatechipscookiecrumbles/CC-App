from . import *

from .Data_Processing import build_gender_sport_summaries, extract_unique_sports_from_rows, combine_financial_columns
from .Excel_Generator import build_total_revenue_sheet





black_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")


def _is_revenue_table_column(column):
    return bool(re.fullmatch(r"\d{1,2}[A-Z]?", str(column)))


def _revenue_column_sort_key(column):
    match = re.fullmatch(r"(\d{1,2})([A-Z]?)", str(column))
    if not match:
        return (999, str(column))
    number, suffix = match.groups()
    return (int(number), suffix)

def safe_sheet_title(title: str) -> str:
    # Replace forbidden characters with underscores
    invalid_chars = r'[\\/*?:\[\]]'
    clean_title = re.sub(invalid_chars, "_", title)
    # Truncate to 31 characters (Excel’s max sheet name length)
    return clean_title[:31]

def safe_write(ws, cell_ref, value):
    """
    Safely writes a value to a worksheet cell.
    Handles merged cells and applies a black fill if value is None, 0, or NaN.
    """
    cell = ws[cell_ref]

    # Function to handle writing and applying fill
    def write_and_fill(target_cell, val):
        if val is None or val == 0 or (isinstance(val, float) and pd.isna(val)):
            target_cell.value = ""
            target_cell.number_format = "@"
            target_cell.fill = black_fill
        else:
            target_cell.value = val

    # If the cell is part of a merged range, write to its top-left cell
    if isinstance(cell, MergedCell):
        for merged_range in ws.merged_cells.ranges:
            if cell.coordinate in merged_range:
                top_left = ws[merged_range.coord.split(":")[0]]
                write_and_fill(top_left, value)
                return
        raise ValueError(f"Cannot write to merged cell {cell_ref}, and no range found.")
    else:
        write_and_fill(cell, value)



def _join_values(values):
    if not values:
        return ""
    return ", ".join(str(value) for value in values)


def write_revenue_validation_sheet(wb, validation_records):
    if not validation_records:
        return

    if "Validation" in wb.sheetnames:
        del wb["Validation"]
    ws = wb.create_sheet("Validation")

    headers = [
        "Institution",
        "File Name",
        "Ticket Sales Status",
        "Ticket Sales Value",
        "Missing Revenue Categories",
        "Found Revenue Categories",
        "Combined Categories",
        "Skipped",
        "Parse Error",
    ]
    ws.append(headers)

    for record in validation_records:
        ws.append(
            [
                record.get("institution_name", ""),
                record.get("filename", ""),
                record.get("ticket_sales_status", ""),
                record.get("ticket_sales_value", ""),
                _join_values(record.get("missing_tables", [])),
                _join_values(record.get("found_tables", [])),
                _join_values(record.get("combined_categories", [])),
                "Yes" if record.get("skipped") else "No",
                record.get("parse_error", ""),
            ]
        )

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="FFBF00", end_color="FFBF00", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    widths = {
        "A": 36,
        "B": 32,
        "C": 20,
        "D": 18,
        "E": 36,
        "F": 36,
        "G": 42,
        "H": 12,
        "I": 44,
    }
    for column, width in widths.items():
        ws.column_dimensions[column].width = width

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def fill_excel_with_data_revenue(df, excel_path, client_uni, ifclient, start_cell="B5", validation_records=None):
    """
    Fills the generated Excel template with extracted and processed data.
    df: a single DataFrame (not dict)
    """

    if "University" in df.columns:
        df = df.set_index("University")

    # Combine financial columns first
    df_processed = combine_financial_columns(df)
    revenue_columns = [
        column
        for column in df_processed.columns
        if _is_revenue_table_column(column)
    ]
    df_processed = df_processed.reindex(
        sorted(revenue_columns, key=_revenue_column_sort_key),
        axis=1,
    )

    wb = load_workbook(excel_path)
    ws = wb.active
    start_col = re.sub(r"\d+", "", start_cell)
    start_row = int(re.sub(r"[A-Za-z]+", "", start_cell))

    # Build total revenue sheet
    build_total_revenue_sheet(ws, f"CONFERENCE - Revenue", max(len(df_processed) - 1, 0), ifclient)

    # Fill client university row
    ws[f"{start_col}4"] = client_uni
    try:
        row = df_processed.loc[[client_uni]]
        row_values = row.values.tolist()[0]
        for i, value in enumerate(row_values):
            col_letter = chr(ord('C') + i)
            safe_write(ws, f"{col_letter}4", value)
    except KeyError:
        row_values = [None] * len(df_processed.columns)
        for i, value in enumerate(row_values):
            col_letter = chr(ord('C') + i)
            safe_write(ws, f"{col_letter}4", value)
        print(f"Error: {client_uni} not found in the DataFrame")

    # Fill remaining universities
    df_remaining = df_processed.drop(client_uni, errors='ignore')
    for r_idx, row_tuple in enumerate(df_remaining.itertuples(index=True, name=None), start=start_row):
        idx = row_tuple[0]
        row_values = row_tuple[1:]
        safe_write(ws, f"{start_col}{r_idx}", idx)
        for c_idx, value in enumerate(row_values, start=column_index_from_string(start_col) + 1):
            col_letter = get_column_letter(c_idx)
            cell_ref = f"{col_letter}{r_idx}"
            is_blank = pd.isna(value) or value == 0 or (isinstance(value, str) and value.strip() == "")
            if is_blank:
                safe_write(ws, cell_ref, None)
                cell = ws[cell_ref]
                cell.fill = black_fill
            else:
                safe_write(ws, cell_ref, value)

    write_revenue_validation_sheet(wb, validation_records)
    wb.save(excel_path)
    print(f"Data saved to {excel_path}")
