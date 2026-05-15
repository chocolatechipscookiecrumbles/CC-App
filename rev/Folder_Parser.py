from . import *
from programlauncher.common.pdf_manifest import build_pdf_manifest
from .config import (
    EXPECTED_REVENUE_TABLE_IDS,
    REVENUE_COMBINATION_DESCRIPTIONS,
    REVENUE_TABLE_LABELS,
)
from .Testextract import extract_summary_totals
from .write_report import write_report


def _ticket_sales_status(parsed_result):
    if "1" not in parsed_result:
        return "missing"
    if parsed_result.get("1") == 0:
        return "found_zero"
    return "found_value"


def _validation_record(record, parsed_result=None, parse_error=None, skipped=False):
    parsed_result = parsed_result or {}
    found_tables = sorted(parsed_result.keys())
    missing_tables = [
        table_id
        for table_id in EXPECTED_REVENUE_TABLE_IDS
        if table_id not in parsed_result
    ]
    return {
        "institution_name": record.institution_name,
        "filename": record.filename,
        "ticket_sales_status": _ticket_sales_status(parsed_result),
        "ticket_sales_value": parsed_result.get("1"),
        "found_tables": found_tables,
        "missing_tables": missing_tables,
        "combined_categories": list(REVENUE_COMBINATION_DESCRIPTIONS.values()),
        "parse_error": parse_error or "",
        "skipped": skipped,
    }

def collect_revenue_across_pdfs(
    folder_path,
    manifest=None,
    summary=None,
    progress_reporter=None,
    cancel_token=None,
):
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
    validation_records = []

    total = len(records)

    for index, record in enumerate(records, start=1):
        if cancel_token and cancel_token.is_cancelled:
            if summary:
                summary.cancelled = True
            break

        filename = record.filename
        institution_name = record.institution_name
        pdf_path = record.path
        if progress_reporter:
            progress_reporter.update(
                current=index,
                total=total,
                institution=institution_name,
                stage="Extracting revenue totals",
                skipped_count=summary.skipped_count if summary else len(not_read),
            )
        try:
            # Run your existing PDF parsing function
            parsed_result = extract_summary_totals(pdf_path)

            if not parsed_result or parsed_result == 1:
                validation_records.append(
                    _validation_record(record, {}, skipped=True)
                )
                if summary:
                    summary.add_skipped(
                        filename,
                        path=pdf_path,
                        institution_name=institution_name,
                        reason="empty_result",
                        stage="revenue_extraction",
                    )
                else:
                    not_read.append(filename)
                continue

            # Extract a clean university name (e.g., remove PDF extension)
            all_data.append({"University": institution_name, **parsed_result})
            validation_records.append(
                _validation_record(record, parsed_result, skipped=False)
            )
            if summary:
                summary.add_processed()

        except Exception as e:
            validation_records.append(
                _validation_record(record, {}, parse_error=str(e), skipped=True)
            )
            if summary:
                summary.add_skipped(
                    filename,
                    path=pdf_path,
                    institution_name=institution_name,
                    reason="parse_error",
                    stage="revenue_extraction",
                    exception_message=str(e),
                )
            else:
                print(f"Error processing {filename}: {e}")

    if summary:
        summary.extra["revenue_validation"] = validation_records

    if not all_data:
        write_report(folder_path, summary.skipped_files if summary else not_read)
        return pd.DataFrame(columns=["University"] + list(REVENUE_TABLE_LABELS.values()))

    df = pd.DataFrame(all_data).set_index("University")

    # Sort alphabetically by university name
    df = df.sort_index()
    write_report(folder_path, summary.skipped_files if summary else not_read)
    return df
