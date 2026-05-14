from . import *
from programlauncher.common.sports import SPORT_PATTERNS

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

def fill_excel_with_data_sportops(df_dict, excel_path, client_uni, menslist , womenslist, ifclient,start_cell="B5"):
    """
    Fills the generated Excel template with extracted data.
    """
    wb = load_workbook(excel_path)
    start_col = re.sub(r"\d+", "", start_cell)  # "B"
    start_row = int(re.sub(r"[A-Za-z]+", "", start_cell))  # 5

    def normalize(s: str) -> str:
        # Lowercase + remove spaces + remove apostrophes only
        return s.lower().replace(" ", "").replace("'", "")

    # Prepare normalized lists
    mens_norm = {normalize(s) for s in menslist}
    womens_norm = {normalize(s) for s in womenslist}
    all_sports_norm = mens_norm | womens_norm  # set union

    # Pre-filter df_dict with exact normalized match
    filtered_dict = {}
    for sport, df in df_dict.items():
        sport_clean = normalize(sport)
        if sport_clean in all_sports_norm:
            filtered_dict[sport] = df

    for sport, df in filtered_dict.items():
        ws = wb.create_sheet(title=safe_sheet_title(sport))
        num = len(df)
        if client_uni in df.index:
            build_totalsports_sheet(ws,f"CONFERENCE - {sport} Sport Operating Budgets",num-1,ifclient)
        else:
            build_totalsports_sheet(ws, f"CONFERENCE - {sport} Sport Operating Budgets", num,ifclient)
        ws[f"{start_col}4"] = client_uni
        try:
            row = df.loc[[client_uni]]
            # df = df.drop(client_uni)
            # row_values = row.values.tolist()

            row_values = row.values.tolist()[0]  # flatten to 1D list
            for i, value in enumerate(row_values):
                col_letter = chr(ord('C') + i)  # start at column C
                #print(repr(value), type(value))
                safe_write(ws, f"{col_letter}4", value)
                #ws[f"{col_letter}4"] = value
                #cell = ws[f"{col_letter}4"]
                '''if value is None or value == 0 or (isinstance(value, float) and pd.isna(value)):
                    cell.value = ""  # optionally set value to empty string
                    cell.fill = black_fill'''
        except KeyError:
            row_values = [None] * len(df.columns)

            # Safely write row values starting from column C
            for i, value in enumerate(row_values):
                col_letter = chr(ord('C') + i)  # start at column C
                safe_write(ws, f"{col_letter}4", value)
            print(f"Error: {client_uni} not found in the DataFrame")

        df_remaining = df.drop(client_uni, errors='ignore')
        for r_idx, row_tuple in enumerate(df_remaining.itertuples(index=True, name=None), start=start_row):
            idx = row_tuple[0]
            row_values = row_tuple[1:]
            # Write index safely
            safe_write(ws, f"{start_col}{r_idx}", idx)

            for c_idx, value in enumerate(row_values, start=column_index_from_string(start_col) + 1):
                col_letter = get_column_letter(c_idx)
                cell_ref = f"{col_letter}{r_idx}"

                is_blank = (
                        pd.isna(value) or  # catches NaN
                        value == 0 or  # catches zero
                        (isinstance(value, str) and value.strip() == "")  # catches empty/whitespace strings
                )

                if is_blank:
                    # write empty safely + black fill
                    safe_write(ws, cell_ref, None)
                    cell = ws[cell_ref]
                    cell.fill = black_fill
                else:
                    safe_write(ws, cell_ref, value)
    men_total, women_total = build_gender_sport_summaries(filtered_dict)
    #print(men_total, women_total)
    men_col = men_total.columns.tolist()
    women_col = women_total.columns.tolist()
    wsm = wb.create_sheet(title="Men's Total")
    wswm = wb.create_sheet(title="Women's Total")
    build_total_sports_total_sheet(wsm, "CONFERENCE - Men's Sport Operating Budgets ", men_col, len(men_total)-1,ifclient)
    build_total_sports_total_sheet(wswm, "CONFERENCE - Women's Sport Operating Budgets ", women_col, len(women_total)-1,ifclient)
    fill_excel_with_data_sportops_total(men_total, women_total,wsm,wswm, client_uni)


    wb.save(excel_path)
    print(f"Data saved to {excel_path}")

def fill_excel_with_data_sportops_total(male_df,female_df, wsm, wswm, client_uni, start_cell="B5"):
    """
    Fills the generated Excel template with extracted data.
    """
    wsmen = wsm
    wswomen = wswm
    wsdf = [(wsmen, male_df, "men"), (wswomen, female_df, "women")]

    start_col = re.sub(r"\d+", "", start_cell)  # "B"
    start_row = int(re.sub(r"[A-Za-z]+", "", start_cell))  # 5

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
    # uni_data = []
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
                if header.strip().lower() not in SPORT_PATTERNS:
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
