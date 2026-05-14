from . import *
from programlauncher.common.pdf_manifest import build_pdf_manifest
from .write_report import write_report


def extract_total_operating_expensesregx(pdf_path):
    pattern = re.compile(r"Total Operating\s*(?:Expenses)?\s*\$([\d,]+(?:\.\d{2})?)\s+Total\s*of\s*Categories\s*20-41A",
                         re.IGNORECASE)
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # print(text)
            if text:
                match = pattern.search(text)
                if match:
                    # Remove commas and convert to int
                    value = int(match.group(1).replace(",", ""))
                    return value
    return None


def parse_folder_toe(folder_path, client_uni, manifest=None):
    data = []  # store (university, value)
    client_value = None
    not_read = []
    # counter = 1

    records = manifest if manifest is not None else build_pdf_manifest(folder_path)

    # Loop PDFs
    for record in records:
        file_name = record.filename
        pdf_path = record.path
        toe_value = extract_total_operating_expensesregx(pdf_path)
        if toe_value is None:
            not_read.append(file_name)
            continue

        university = record.institution_name

        if university == client_uni:
            client_value = toe_value  # store but don’t list below
        else:
            data.append((university, toe_value))

    df = pd.DataFrame(data, columns=["University", "TOE"])
    df = df.sort_values(by="University")
    write_report(folder_path, not_read)

    return df, len(df) + 1, client_value


def set_border(cell, **sides):
    cell.border = Border(
        left=sides.get("left", cell.border.left),
        right=sides.get("right", cell.border.right),
        top=sides.get("top", cell.border.top),
        bottom=sides.get("bottom", cell.border.bottom)
    )


def generate_template_excel(output_path, num_items, ifclient):
    """
    Creates a styled Excel file with headers, merged cells, and placeholders
    for num_items worth of data rows, plus Average and Median rows at the bottom.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Total Operating Expenses"

    # --- Styles ---
    bold_font = Font(bold=True)
    header_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
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

    # --- Header ---
    ws.merge_cells("B2:C2")
    ws["B2"] = "CONFERENCE - Total Athletic Budget"
    ws["B2"].border = thick_all_border_style
    ws["B2"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["B2"].alignment = center_align
    ws["B2"].fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")

    # Column headers
    ws["B3"] = "Institution"
    ws["C3"] = "Budget"
    ws["B4"] = "Client Name"

    for cell in ["B3", "C3"]:
        ws[cell].font = bold_font
        ws[cell].fill = header_fill
        ws[cell].alignment = center_align
        ws[cell].fill = PatternFill(start_color="FFBF00", end_color="FFBF00", fill_type="solid")

    for cell in ["B4", "C4"]:
        ws[cell].font = bold_font
        ws[cell].fill = PatternFill(start_color="BFBFBF", end_color="BFBFBF", fill_type="solid")

    # Adjust column widths
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["C"].width = 20

    # --- Data Section ---
    start_row = 5
    end_row = start_row + num_items - 1  # Last data row
    avg_row = end_row + 1
    median_row = end_row + 2
    rank_row = end_row + 3

    # Labels for Average & Median
    ws[f"B{avg_row}"] = "Average"
    ws[f"B{median_row}"] = "Median"
    ws[f"B{avg_row}"].font = bold_font
    ws[f"B{median_row}"].font = bold_font
    ws[f"B{rank_row}"] = "Rank"
    ws[f"B{rank_row}"].font = bold_font

    # Formulas
    if ifclient:
        ws[f"C{avg_row}"] = f"=AVERAGE(C{start_row - 1}:C{end_row})"
        ws[f"C{median_row}"] = f"=MEDIAN(C{start_row - 1}:C{end_row})"
        ws[f"C{rank_row}"] = f"=RANK(C{start_row - 1},C{start_row - 1}:C{end_row})"
    else:
        ws[f"C{avg_row}"] = f"=AVERAGE(C{start_row}:C{end_row})"
        ws[f"C{median_row}"] = f"=MEDIAN(C{start_row}:C{end_row})"
        ws[f"C{rank_row}"] = f"=RANK(C{start_row - 1},C{start_row - 1}:C{end_row})"

    # Borders
    # Left and right outline borders
    highlight_fill = PatternFill(start_color="FFBF00", end_color="FFBF00", fill_type="solid")
    for row in range(start_row - 1, rank_row + 1):
        ws[f"C{row}"].alignment = center_align
        ws[f"C{row}"].border = thick_lr_border_style
        ws[f"B{row}"].border = thick_lr_border_style

    for cell in [rank_row, avg_row, median_row]:
        for col in ["B", "C"]:
            ws[f"{col}{cell}"].font = bold_font
            ws[f"B{cell}"].alignment = right_align
            ws[f"{col}{cell}"].fill = highlight_fill
            ws[f"{col}{cell}"].border = thick_lr_border_style

    for col in ["B", "C"]:
        set_border(ws[f"{col}{avg_row}"], top=Side(style="medium", color="000000"))
        set_border(ws[f"{col}{rank_row}"], bottom=Side(style="medium", color="000000"))

    for cell in ["B3", "C3", "B4", "C4"]:
        ws[f"{cell}"].border = thick_all_border_style

    wb.save(output_path)
    print(f"Template created: {output_path}")


def col_to_num(col):
    """
    Converts Excel column letter(s) to number.
    'A' -> 1, 'B' -> 2, ..., 'Z' -> 26, 'AA' -> 27, etc.
    """
    num = 0
    for c in col.upper():
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num


def fill_excel_with_data(df, excel_path, client_uni, client_value, num_items, start_cell="B5"):
    wb = load_workbook(excel_path)
    ws = wb.active
    bold_font = Font(bold=True)

    # --- Parse start_cell safely ---
    start_col = re.sub(r"\d+", "", start_cell)  # "B"
    row_digits = re.sub(r"[A-Za-z]+", "", start_cell)  # "5"
    start_row = int(row_digits) if row_digits else 5  # fallback if empty
    end_row = start_row + num_items - 1

    for r_idx, row in enumerate(df.itertuples(index=False), start=start_row):
        for c_idx, value in enumerate(row, start=2):
            # ws.cell(row=r_idx, column=c_idx, value=value)
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            if c_idx == col_to_num(start_col) + 1:  # second column (TOE)
                cell.number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'

    # --- Client row (B4 / C4) ---
    ws["B4"] = client_uni
    ws["B4"].font = bold_font
    ws["C4"] = client_value
    ws["C4"].font = bold_font
    ws["C4"].number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'

    for row in range(end_row, end_row + 2):
        cell = ws[f"C{row}"]
        # cell.number_format = numbers.FORMAT_CURRENCY_USD_SIMPLE
        # cell.number_format = '"$"#,##0'
        cell.number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'

    wb.save(excel_path)
    print(f"Data saved with client info to {excel_path}")
