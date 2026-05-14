from . import *
from programlauncher.common.sports import SPORT_PATTERNS

black_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")

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


def fill_excel_with_data_scholar(male_df,female_df, excel_path, client_uni, start_cell="B5"):
    """
    Fills the generated Excel template with extracted data.
    """
    wb = load_workbook(excel_path)
    wsmen = wb["Men's Sports"]
    wswomen = wb["Women's Sports"]
    wsdf = [(wsmen, male_df, "men"), (wswomen, female_df, "women")]

    start_col = re.sub(r"\d+", "", start_cell)  # "B"
    start_row = int(re.sub(r"[A-Za-z]+", "", start_cell))  # 5

    # Build header lookup {sport_name.lower(): column_letter}
    headers_men = {
        wsmen.cell(row=3, column=col).value.lower(): get_column_letter(col)
        for col in range(3, wsmen.max_column + 1)
        if wsmen.cell(row=3, column=col).value
    }
    headers_women = {
        wswomen.cell(row=3, column=col).value.lower(): get_column_letter(col)
        for col in range(3, wswomen.max_column + 1)
        if wswomen.cell(row=3, column=col).value
    }
    #uni_data = []
    for worksheet, df, gender in wsdf:
        current_row = start_row
        headers = headers_men if gender == "men" else headers_women

        for row_tuple in df.itertuples(index=True, name=None):
            index = row_tuple[0]
            row_values = dict(zip(df.columns, row_tuple[1:]))
            # Clean university name
            university = re.sub(r",\s*FY\d{2,4}$", "", index.strip(), flags=re.IGNORECASE)

            # Normalize for comparison
            uni_clean = university.strip().lower()
            client_clean = client_uni.strip().lower()

            # Choose the correct target row
            if uni_clean == client_clean:
                target_row = 4  # or whatever row you want for client_uni
                worksheet[f"{start_col}{target_row}"] = university
            else:
                target_row = current_row
                worksheet[f"{start_col}{target_row}"] = university

            # For each header (Excel column) we’re supposed to write
            for header, col_letter in headers.items():
                if header.strip().lower() == "total":
                    continue

                # Find matching column name from df using SPORT_PATTERNS
                match_col = None
                for sport in df.columns:
                    sport_lower = sport.lower()
                    if SPORT_PATTERNS[header].search(sport_lower):
                        match_col = sport
                        break

                # Safely get value — blank if no column or NaN
                if match_col and match_col in row_values and not pd.isna(row_values[match_col]):
                    value = row_values[match_col]
                else:
                    value = ""

                safe_write(worksheet, f"{col_letter}{target_row}", value)

            # Only increment for non-client rows
            if uni_clean != client_clean:
                current_row += 1
    wb.save(excel_path)
    print(f"Data saved to {excel_path}")
