from __future__ import annotations
from . import *
from .config import SPORTOPS_TABLE_NAMES


table_names = SPORTOPS_TABLE_NAMES


# flexible regexes
#TITLE_RE = re.compile(r'^\s*(\d{1,2})\s+([A-Za-z][A-Za-z0-9 &,\-]+)', re.I)
'''
TITLE_RE = re.compile(
    r'^\s*'                                # leading whitespace
    r'(\d{2})'                           # group 1: section number (2 digits)
    r'\s+'                                 # at least one space
    r'((?:[A-Za-z][A-Za-z0-9&,\-\/]*\s*){1,6})'  # group 2: title (1-6 word-like tokens)
    r'\s*,?\s*'                            # optional comma + spaces
    r'\$?([\d,]+(?:\.\d+)?)?'              # group 3: optional $amount (commas/decimals)
    r'\s*(.*)$'                            # group 4: rest of line (description)
, re.I)'''
TITLE_RE = re.compile(
    r'^\s*(\d{2})\s+([^$]+)\$.*(?:Input)?',
    re.I
)
# we'll test header both with whitespace-insensitive and normal regex
HEADER_WORDS = "Expenses by Object of Expenditure"
#HEADER_RE = re.compile(r'Expenses\s*by\s*Object\s*of\s*Expenditure', re.I)
# This allows any whitespace (spaces, newlines, tabs) between words
#HEADER_RE = re.compile(r'Expenses[\s\n]*by[\s\n]*Object[\s\n]*of[\s\n]*Expenditure', re.I)
HEADER_RE = re.compile(r'Expenses[\s\n]*by[\s\n]*Object[\s\n]*of[\s\n]*(?:Expenditure\b)?', re.I)
# row regex: category + up to 3 numeric columns (commas allowed)
#ROW_RE = re.compile(r'^\s*([A-Za-z0-9&\-,\s\./]+?)\s+([\d,]+)?\s*([\d,]+)?\s*([\d,]+)?\s*$')
number = r'-?\s*\d[\d,]*(?:\.\d+)?'
ROW_RE = re.compile(
    rf'^\s*([A-Za-z0-9&\-,\s\./]+?)\s+({number})?\s*({number})?\s*({number})?\s*$'
)


# Define gender keyword lists (can be expanded easily)
MEN_KEYWORDS = ["baseball", "football","rifle","crew"]
WOMEN_KEYWORDS = ["softball", "beach volleyball", "field hockey", "bowling", "equestrian", "rugby", "rowing"]

def detect_gender_from_keywords(cat: str,
                                men_keywords=MEN_KEYWORDS,
                                women_keywords=WOMEN_KEYWORDS) -> str | None:
    """
    Return 'men', 'women', or None based on the presence of keywords in the category text.
    Checks against customizable keyword lists.
    """
    cat_lower = cat.lower()
    if any(kw in cat_lower for kw in women_keywords):
        return "women"
    if any(kw in cat_lower for kw in men_keywords):
        return "men"
    return None

def contains_all_keywords(lines, keywords, window_size=10):
    """
    Checks whether a sequence of consecutive lines contains all the keywords.

    Args:
        lines (list[str]): The list of lines to check.
        keywords (list[str]): The keywords to search for.
        window_size (int): Number of lines to check at a time.

    Returns:
        list[tuple[int, str]]: A list of (start_index, combined_window_string) where
        all keywords were found within that window.
    """
    matches = []

    # Normalize keywords to lowercase for case-insensitive matching
    keywords = [kw.lower() for kw in keywords]

    for i in range(len(lines) - window_size + 1):
        # Combine the current window of lines into one string
        window_text = "".join(lines[i:i + window_size]).lower()

        # Check if all keywords are present in this window
        if all(kw in window_text for kw in keywords):
            return True
    return False

def _squish(s: str) -> str:
    """Lowercase and remove whitespace/punctuation that's likely collapsed by text extraction."""
    return re.sub(r'[\s\.,\$]+', '', (s or "").lower())

def _parse_table_lines(lines, start_idx, max_lines_parsed=100):
    parsed_rows = []
    empty_line_streak = 0

    for k in range(start_idx, min(len(lines), start_idx + max_lines_parsed)):
        rowline = lines[k].strip()
        if not rowline:
            empty_line_streak += 1
            # if many blank lines in a row, assume table ended
            if empty_line_streak >= 3:
                break
            continue
        empty_line_streak = 0

        # If hits clear footer or unrelated section text, break (heuristic)
        if re.search(r'page\s*\d+|reportinginstitution|ncaamembership', rowline, re.I):
            break

        rm = ROW_RE.match(rowline)
        if not rm:
            # stop if we see no digits in this line and the following few lines also have no digits
            number_pattern = r'-?\d+(\.\d+)?'

            if not re.search(number_pattern, rowline):
                next_chunk = " ".join(lines[k + 1:k + 20])
                if not re.search(number_pattern, next_chunk):
                    break
                else:
                    continue
            else:
                continue

        cat = rm.group(1).strip()
        nums = []

        for g in (rm.group(2), rm.group(3), rm.group(4)):
            if g:
                nums.append(int(g.replace(",", "")))
            else:
                nums.append(None)

        gender = detect_gender_from_keywords(cat)
        non_null_count = sum(n is not None for n in nums)

        if gender and non_null_count == 1:
            # Only one value -> put it in the correct gender column
            men_val, women_val, not_allocated_val = None, None, None
            value = next(n for n in nums if n is not None)
            if gender == "men":
                men_val = value
                parsed_rows.append([cat, men_val, women_val, not_allocated_val])
            elif gender == "women":
                women_val = value
                parsed_rows.append([cat, men_val, women_val, not_allocated_val])
            else:
                parsed_rows.append([cat] + nums)
        else:
            # Fallback: keep as-is
            parsed_rows.append([cat] + nums)

    if not parsed_rows:
        return None

    cols = ['category', 'men', 'women', 'not_allocated']
    # ensure every row has exactly 4 cells (pad if necessary)
    parsed_norm = []
    for r in parsed_rows:
        while len(r) < 4:
            r.append(None)
        parsed_norm.append(r[:4])
    found_df = pd.DataFrame(parsed_norm, columns=cols)
    return found_df.fillna(0)

def extract_tables_by_title(pdf_path, lookahead_lines=20, header_phrase=HEADER_WORDS):
    """
    Return dict mapping title_key ("21 Guarantees") -> pandas.DataFrame for the nearest table below that title.
    """
    results = {}
    HEADER_WORDS = "Expenses by Object of Expenditure"
    header_squished = _squish(HEADER_WORDS)

    with pdfplumber.open(pdf_path) as pdf:
        for pnum, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text == '':
                return 1
            #print(text)
            lines = text.splitlines()


            # precompute squished lines for fast header matching
            squished_lines = [_squish(l) for l in lines]
            try:
                page_tables = [t.extract() for t in page.find_tables()]
            except Exception:
                # table detection can throw if page layout is odd; fallback parsing below still applies
                page_tables = []

            for i, line in enumerate(lines):
                # detect "21 Guarantees" like title line
                # 1) Fix common smashed words: insert a space between lower->Upper (SportsEquipment -> Sports Equipment)
                line = re.sub(r'([a-z])([A-Z])', r'\1 \2', line)

                # 2) Collapse multiple whitespace into single spaces (normalizes weird line breaks)
                line = " ".join(line.split())
                m = TITLE_RE.match(line)
                if not m:
                    #print(line)
                    continue
                title_num, title_text = m.group(1), m.group(2).strip()
                #print(title_num, title_text)
                title_key = f"{title_num} {title_text}"

                if not any(title_num.startswith(name.split()[0]) for name in table_names):
                    #print(title_num)
                    continue

                # lookahead chunk (next few lines) - test both normal and squished match
                #look_chunk = " ".join(lines[i+1 : i+1+lookahead_lines])
                #squished_chunk = _squish(look_chunk)

                # if header phrase not found in next few lines, skip (change this to if contain words)
                #if not (HEADER_RE.search(look_chunk) or header_squished in squished_chunk):
                    #continue

                # 1) Prefer structural table detection: find_tables() -> check header row
                found_df = None
                for tbl in page_tables:
                    if not tbl or not tbl[0]:
                        continue
                    header_row_combined = " ".join([str(x) for x in tbl[0] if x])
                    if HEADER_RE.search(header_row_combined) or header_squished in _squish(header_row_combined):
                        # build dataframe and normalize column names
                        df = pd.DataFrame(tbl[1:], columns=tbl[0])
                        df.columns = [ (c.strip() if c else f"col{i}") for i,c in enumerate(df.columns) ]
                        found_df = df.fillna("")
                        break

                # 2) Fallback: parse lines after the header line
                if found_df is None:
                    # find the index of the actual header line among the lookahead lines
                    header_idx = None
                    for j in range(i+1, min(len(lines), i+1+lookahead_lines)):
                        if HEADER_RE.search(lines[j]) or header_squished in _squish(lines[j]):
                            header_idx = j
                            break
                    start_idx = (header_idx + 1) if header_idx is not None else i+1

                    found_df = _parse_table_lines(lines, start_idx)

                if found_df is not None:
                    results[title_num] = found_df
    if not results:
        return 1
    # after all processing, before returning, only keep the subtotal column for checksum
    for key, df in results.items():
        # Create mask for rows to EXCLUDE
        category_lower = df['category'].str.lower().str.strip()

        # Exclude these specific patterns
        exclude_mask = (
                category_lower.str.contains(r'expenses?\s+not\s+related', regex=True, na=False) |
                category_lower.str.contains(r'^total\s+expenses?$', regex=True, na=False) |
                category_lower.str.contains(r'^grand\s+total$', regex=True, na=False)
        )

        # Keep everything except excluded rows
        results[key] = df.loc[~exclude_mask].copy()

    return results
