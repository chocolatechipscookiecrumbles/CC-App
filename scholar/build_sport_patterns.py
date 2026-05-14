from . import *

def build_sport_patterns(ws, header_row=3):
    """
    Build regex patterns for each header in a sheet.
    Default: exact match on header name.
    Special cases can be overridden.
    """
    patterns = {}

    for col in range(3, ws.max_column + 1):  # C onward
        header = ws.cell(row=header_row, column=col).value
        if not header:
            continue

        header_lower = header.lower()

        # --- Default: exact match ---
        pattern = re.compile(rf"^{re.escape(header_lower)}$", re.I)

        # --- Special cases ---
        if header_lower == "xc/tf":
            pattern = re.compile(r"(track\s*and\s*field|cross\s*country|xc)", re.I)

        patterns[header_lower] = pattern

    return patterns