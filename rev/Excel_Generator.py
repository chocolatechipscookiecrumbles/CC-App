from . import *



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

def set_border(cell, **sides):
    cell.border = Border(
        left=sides.get("left", cell.border.left),
        right=sides.get("right", cell.border.right),
        top=sides.get("top", cell.border.top),
        bottom=sides.get("bottom", cell.border.bottom)
    )

def build_toe_sports_sheet():
    wb = Workbook()



def build_total_revenue_sheet(ws, title, num_items, ifclient):
    """
    Build a single sheet with headers, formulas, and formatting.
    """
    # --- Styles ---
    metrics = [
    "Ticket Sales",
    "Institutional/ Government Support",
    "Student Fees",
    "Guarantees",
    "Contributions",
    "Media Rights",
    "NCAA/Conference",
    "Program, Novelty, Parking and Concession Sales",
    "Corporate Sponsorship",
    "Conference/Bowl",
    "Other"
]

    target_tables = {
        "1": "Ticket Sales",
        "2": "Direct State or Other",
        "3": "Student Fees",
        "4": "Direct Institutional",
        "7": "Guarantees",
        "8": "Contributions",
        "11": "Media Rights",
        "12": "NCAA Distributions",
        "13": "Conference Distributions",
        "13A": "Conference Distributions of Football Bowl Generated Revenue",
        "14": "Program, Novelty, Parking and Concession Sales",
        "15": "Royalties, Licensing, Advertisement and Sponsorships",
        "18": "Other Operating",
        "19": "Football Bowl"
    }

    # --- Data Section ---
    start_row = 5
    end_row = start_row + num_items - 1
    avg_row = end_row + 1
    median_row = end_row + 2
    rank_row = end_row + 3

    # All Borders
    for row in range(2, rank_row + 1):
        for col in range(2, 2 + len(metrics) + 2):
            cell = ws[f"{get_column_letter(col)}{row}"]
            if start_row-1 <= row < rank_row and col > 2:
                cell.number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'
            if col == 2 or col == 2 + len(metrics) + 1:
                cell.border = thick_lr_border_style
            else:
                cell.border = border_style

    # --- Header ---
    last_col_letter = get_column_letter(len(metrics) + 3)  # B + sports + Total
    ws.merge_cells(f"B2:{last_col_letter}2")
    ws["B2"] = title
    ws["B2"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["B2"].alignment = center_align
    ws["B2"].fill = black_fill
    ws["B2"].border = thick_lr_border_style

    # Column headers
    headers = ["Institution"] + metrics + ["Total"]
    for idx, text in enumerate(headers, start=2):  # B=2
        cell3 = ws.cell(row=3, column=idx, value=text)
        cell4 = ws.cell(row=4, column=idx, value=None)
        cell4.fill = client_fill
        cell3.fill = orange_fill
        cell3.alignment = center_align
        cell3.font = bold_font
        cell4.font = bold_font

    ws["B4"] = "Client Name"
    ws["B4"].font = bold_font

    # Adjust column widths
    ws.column_dimensions["B"].width = 40
    for col in range(3, 2 + len(metrics) + 2):
        if col in (3, 5, 6, 7, 8, 13, 14):
            ws.column_dimensions[get_column_letter(col)].width = 14
        elif col == 2 + len(metrics) + 1:
            ws.column_dimensions[get_column_letter(col)].width = 25
        else:
            ws.column_dimensions[get_column_letter(col)].width = 30

    # Labels
    for r, label in [(avg_row, "Average"), (median_row, "Median"), (rank_row, "Rank")]:
        ws[f"B{r}"] = label
        ws[f"B{r}"].font = bold_font

        # Formulas per column and formatting
        for col in range(2, 3 + len(metrics) + 1):  # metrics columns
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
                ws[f"{letter}{avg_row}"].number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'
                ws[f"{letter}{median_row}"].number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'
                for i in (avg_row, median_row, rank_row):
                    ws[f"{letter}{i}"].fill = orange_fill
                    ws[f"{letter}{i}"].alignment = center_align
                    ws[f"{letter}{i}"].font = bold_font

    # Total column
    total_col = get_column_letter(2 + len(metrics) + 1)  # last col
    for row in range(start_row-1, avg_row):
        ws[f"{total_col}{row}"] = f"=SUM(C{row}:{get_column_letter(2+len(metrics))}{row})"
        ws[f"{total_col}{row}"].alignment = center_align
        ws[f"{total_col}{row}"].font = bold_font
        ws[f"{total_col}{row}"].number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'

    for col in range(2, 2 + len(metrics) + 2):
        set_border(ws[f"{get_column_letter(col)}3"], top=Side(style="medium", color="000000"),bottom=Side(style="medium"))
        set_border(ws[f"{get_column_letter(col)}4"], bottom=Side(style="medium", color="000000"),top=Side(style="medium", color="000000"))
        set_border(ws[f"{get_column_letter(col)}{avg_row}"], top=Side(style="medium", color="000000"))
        set_border(ws[f"{get_column_letter(col)}{rank_row}"], bottom=Side(style="medium", color="000000"))

    # Conditional Formatting
    '''ws.conditional_formatting.add(
        f"C{start_row}:N{end_row}",  # data rows only
        FormulaRule(
            formula=[f'OR(C{start_row}=0,C{start_row}="")'],  # top-left cell of the range
            fill=black_fill
        )
    )'''


def generate_template_excel_revenue(output_path):
    wb = Workbook()

    wb.save(output_path)
    print(f"Template created: {output_path}")
#sports_titles = extract_unique_sports_from_rows(extract_tables_by_title("FRS Reports (FY24) copy/San Jose State University, FY24.pdf"))
#generate_template_excel_totalsports("textoutputwithM.xlsx",10,sports_titles,"San Jose State University")
#generate_template_excel_totalsports("TestTotal.xlsx", 10)