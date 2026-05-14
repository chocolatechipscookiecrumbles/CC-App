from . import *
from .config import REVENUE_TABLE_LABELS

target_tables = REVENUE_TABLE_LABELS

def extract_summary_totals(pdf_path):
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # normalize whitespace
    text = re.sub(r"[ \t\u00A0]+", " ", text)

    # locate summary block
    start = re.search(r"Revenue\s*/\s*Expense\s+Summary", text, re.IGNORECASE)
    if start:
        start_idx = start.start()
    else:
        start_idx = 0  # fallback: start from beginning

    # set end boundary
    end_match = re.search(
        r"\b\d+\s*(?:\w+\s*){1,5}Athletic\s*Student\s*Aid\b",  # adjust {1,5} for possible extra words
        text,
        re.IGNORECASE
    )
    if end_match:
        end_idx = start_idx + end_match.start()
    else:
        end_idx = start_idx + 10000  # fallback

    summary_block = text[start_idx:end_idx]

    # find all potential matches: ID, name, $value (allow ID optional)
    pattern = re.compile(
        r"(?:\b(\d{1,2}[A-Z]?)\b\s*)?"       # optional ID
        r"([A-Za-z0-9 ,()./&\-]{3,80}?)"     # name/description
        r"\s*\$([\d,]{1,15})",               # dollar value
        re.IGNORECASE
    )
    #print(summary_block)
    for m in pattern.finditer(summary_block):
        table_id, name, value = m.groups()
        value_int = int(value.replace(",", ""))

        # normalize ID if exists
        if table_id:
            table_id = table_id.strip().upper()
            if table_id in target_tables:
                results[table_id] = value_int
                continue  # matched by ID

        # fallback: match by name overlap
        name_words = set(re.findall(r"\w+", name.lower()))
        for k, label in target_tables.items():
            label_words = set(re.findall(r"\w+", label.lower()))
            if len(name_words & label_words) >= 1:
                if k not in results:
                    results[k] = value_int
                break

    return results

#print(extract_summary_totals("Utah State University, FY24 copy.pdf"))
