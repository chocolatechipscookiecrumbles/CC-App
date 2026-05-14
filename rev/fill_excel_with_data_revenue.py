from . import *

from .Data_Processing import build_gender_sport_summaries, extract_unique_sports_from_rows, combine_financial_columns
from .Excel_Generator import build_total_revenue_sheet





black_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")

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



def fill_excel_with_data_revenue(df, excel_path, client_uni, ifclient, start_cell="B5"):
    """
    Fills the generated Excel template with extracted and processed data.
    df: a single DataFrame (not dict)
    """

    # Combine financial columns first
    df_processed = combine_financial_columns(df)
    df_processed = df_processed.reindex(sorted(df_processed.columns, key=lambda x: int(x)), axis=1)

    wb = load_workbook(excel_path)
    ws = wb.active
    start_col = re.sub(r"\d+", "", start_cell)
    start_row = int(re.sub(r"[A-Za-z]+", "", start_cell))

    # Build total revenue sheet
    build_total_revenue_sheet(ws, f"CONFERENCE - Revenue", len(df_processed) - 1, ifclient)

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

    wb.save(excel_path)
    print(f"Data saved to {excel_path}")
