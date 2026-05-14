from . import *
from programlauncher.common.pdf_manifest import build_pdf_manifest
from .config import REVENUE_TABLE_LABELS
from .Testextract import extract_summary_totals
from .write_report import write_report

def collect_revenue_across_pdfs(folder_path, manifest=None):
    """
    Parse all PDFs in a folder using extract_tables_by_title and aggregate results.

    Returns:
        dict[str, pd.DataFrame]
        Key = sport name (or sport + " (Men)" / " (Women)" if split by gender)
        Value = dataframe where:
            - Rows = pdf filenames (universities)
            - Columns = table titles from extract_tables_by_title()
            - Cell = numeric value (or NaN if not present)
    """

    all_data = []
    not_read = []
    records = manifest if manifest is not None else build_pdf_manifest(folder_path)

    for record in records:
        filename = record.filename
        institution_name = record.institution_name
        pdf_path = record.path
        try:
            # Run your existing PDF parsing function
            parsed_result = extract_summary_totals(pdf_path)

            if not parsed_result or parsed_result == 1:
                not_read.append(filename)
                continue

            # Extract a clean university name (e.g., remove PDF extension)
            all_data.append({"University": institution_name, **parsed_result})

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    if not all_data:
        return pd.DataFrame(columns=["University"] + list(REVENUE_TABLE_LABELS.values()))

    df = pd.DataFrame(all_data).set_index("University")

    # Sort alphabetically by university name
    df = df.sort_index()
    write_report(folder_path, not_read)
    return df
