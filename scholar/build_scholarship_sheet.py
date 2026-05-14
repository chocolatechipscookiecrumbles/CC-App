from . import *

def normalize_string(s):
    # Remove whitespace, convert to lowercase, remove punctuation/numbers
    return re.sub(r'[^a-zA-Z]', '', s.strip().lower())

def set_border(cell, **sides):
    cell.border = Border(
        left=sides.get("left", cell.border.left),
        right=sides.get("right", cell.border.right),
        top=sides.get("top", cell.border.top),
        bottom=sides.get("bottom", cell.border.bottom)
    )

def build_scholarship_sheet(ws, title, sports, num_items, ifclient):
    """
    Build a single sheet with scholarship headers, formulas, and formatting.
    """
    # --- Styles ---
    bold_font = Font(bold=True)
    orange_fill = PatternFill(start_color="FFBF00", end_color="FFBF00", fill_type="solid")
    client_fill = PatternFill(start_color="BFBFBF", end_color="BFBFBF", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    border_style = Border(
        left=Side(style="thin", color="000000"),
        right=Side(style="thin", color="000000"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="thin", color="000000")
    )
    all_border_style = Border(
        left=Side(style="thin", color="000000"),
        right=Side(style="thin", color="000000"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="thin", color="000000")
    )
    thick_all_border_style = Border(
        left=Side(style="medium", color="000000"),
        right=Side(style="medium", color="000000"),
        top=Side(style="medium", color="000000"),
        bottom=Side(style="medium", color="000000")
    )
    thick_lr_border_style = Border(
        left=Side(style="medium", color="000000"),
        right=Side(style="medium", color="000000"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="thin", color="000000")
    )
    thick_t_border_style = Border(
        left=Side(style="thin", color="000000"),
        right=Side(style="thin", color="000000"),
        top=Side(style="medium", color="000000"),
        bottom=Side(style="thin", color="000000")
    )
    thick_b_border_style = Border(
        left=Side(style="thin", color="000000"),
        right=Side(style="thin", color="000000"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="medium", color="000000")
    )
    black_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")

    start_row = 5
    end_row = start_row + num_items - 1
    avg_row = end_row + 1
    median_row = end_row + 2
    rank_row = end_row + 3

    # All Borders
    for row in range(2, rank_row + 1):
        for col in range(2, 2 + len(sports) + 2):
            cell = ws[f"{get_column_letter(col)}{row}"]
            if start_row - 1 <= row < rank_row and col > 2:
                cell.alignment = center_align
            if col == 2 or col == 2 + len(sports) + 1:
                cell.border = thick_lr_border_style
            else:
                cell.border = border_style

    # --- Header ---
    last_col_letter = get_column_letter(len(sports) + 3)  # B + sports + Total
    ws.merge_cells(f"B2:{last_col_letter}2")
    ws["B2"] = title
    ws["B2"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["B2"].alignment = center_align
    ws["B2"].fill = black_fill
    ws["B2"].border = thick_all_border_style

    # Column headers
    headers = ["Institution"] + sports + ["Total"]
    for idx, text in enumerate(headers, start=2):  # B=2
        cell3 = ws.cell(row=3, column=idx, value=text)
        cell4 = ws.cell(row=4, column=idx, value=text)
        cell4.fill = client_fill
        cell3.font = bold_font
        cell4.font = bold_font
        cell3.fill = orange_fill
        cell3.alignment = center_align

    ws["B4"] = "Client Name"
    ws["B4"].font = bold_font
    #ws["B4"].fill = client_fill
    #ws["B4"].alignment = center_align

    # Adjust column widths
    ws.column_dimensions["B"].width = 40
    for col in range(3, 2 + len(sports) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 20

    # --- Data Section ---


    # Labels
    for r, label in [(avg_row, "Average"), (median_row, "Median"), (rank_row, "Rank")]:
        ws[f"B{r}"] = label
        ws[f"B{r}"].font = bold_font

    # Formulas per column
    for col in range(2, 3 + len(sports) + 1):  # sports columns
        letter = get_column_letter(col)
        if col == 2:
            ws[f"{letter}{avg_row}"].fill = orange_fill
            ws[f"{letter}{median_row}"].fill = orange_fill
            ws[f"{letter}{rank_row}"].fill = orange_fill
            ws[f"{letter}{avg_row}"].alignment = right_align
            ws[f"{letter}{median_row}"].alignment = right_align
            ws[f"{letter}{rank_row}"].alignment = right_align
        else:
            if ifclient:
                ws[f"{letter}{avg_row}"] = f"=AVERAGE({letter}{start_row - 1}:{letter}{end_row})"
                ws[f"{letter}{median_row}"] = f"=MEDIAN({letter}{start_row - 1}:{letter}{end_row})"
                ws[f"{letter}{rank_row}"] = f"=RANK({letter}{start_row - 1},{letter}{start_row - 1}:{letter}{end_row})"
            else:
                ws[f"{letter}{avg_row}"] = f"=AVERAGE({letter}{start_row}:{letter}{end_row})"
                ws[f"{letter}{median_row}"] = f"=MEDIAN({letter}{start_row}:{letter}{end_row})"
                ws[f"{letter}{rank_row}"] = f"=RANK({letter}{start_row - 1},{letter}{start_row - 1}:{letter}{end_row})"
            '''ws[f"{letter}{rank_row}"].alignment = center_align
            ws[f"{letter}{avg_row}"].alignment = center_align
            ws[f"{letter}{median_row}"].alignment = center_align'''
            for i in (avg_row, median_row, rank_row):
                ws[f"{letter}{i}"].fill = orange_fill
                ws[f"{letter}{i}"].alignment = center_align
                ws[f"{letter}{i}"].font = bold_font

    # Total column
    total_col = get_column_letter(2 + len(sports) + 1)  # last col
    for row in range(start_row - 1, avg_row):
        ws[f"{total_col}{row}"] = f"=SUM(C{row}:{get_column_letter(2 + len(sports))}{row})"
        ws[f"{total_col}{row}"].alignment = center_align
        ws[f"{total_col}{row}"].font = bold_font

    for col in range(2, 2 + len(sports) + 2):
        set_border(ws[f"{get_column_letter(col)}3"], top=Side(style="medium", color="000000"),
                   bottom=Side(style="medium"))
        set_border(ws[f"{get_column_letter(col)}4"], bottom=Side(style="medium", color="000000"),
                   top=Side(style="medium", color="000000"))
        set_border(ws[f"{get_column_letter(col)}{avg_row}"], top=Side(style="medium", color="000000"))
        set_border(ws[f"{get_column_letter(col)}{rank_row}"], bottom=Side(style="medium", color="000000"))

def generate_template_excel_scholar(output_path, num_items,sports_list_men, sports_list_women,ifclient):
    wb = Workbook()

    # Men’s sheet
    ws_men = wb.active
    ws_men.title = "Men's Sports"
    '''remove_sports_men = ['beach volleyball', 'bowling', 'field hockey', 'softball', 'water polo']
    normalized_remove_set = {normalize_string(item) for item in remove_sports_men}

    filtered_list_men = [item for item in sports_list
                     if normalize_string(item) not in normalized_remove_set]'''
    build_scholarship_sheet(ws_men, "CONFERENCE - Men's Scholarships",
                            sports_list_men,
                            num_items,ifclient)

    # Women’s sheet
    ws_women = wb.create_sheet(title="Women's Sports")
    build_scholarship_sheet(ws_women, "CONFERENCE - Women's Scholarships",
                            sports_list_women,
                            num_items,ifclient)

    wb.save(output_path)
    print(f"Template created: {output_path}")