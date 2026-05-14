import csv

from programlauncher.common.report_log import write_report
from programlauncher.common.run_summary import SkippedFileRecord, WorkflowRunSummary
from programlauncher.common import settings


def test_run_summary_tracks_processed_skipped_and_duration():
    summary = WorkflowRunSummary("Revenue", "/tmp/pdfs", pdfs_found=2)
    summary.add_processed()
    summary.add_skipped(
        "missing.pdf",
        institution_name="Example University",
        reason="section_not_found",
        stage="revenue_extraction",
    )
    summary.finish(output_path="/tmp/revenue.xlsx")

    assert summary.processed_count == 1
    assert summary.skipped_count == 1
    assert summary.reason_counts() == {"section_not_found": 1}
    assert summary.duration_seconds is not None
    assert summary.output_path == "/tmp/revenue.xlsx"


def test_write_report_outputs_structured_csv(tmp_path):
    record = SkippedFileRecord(
        filename="bad.pdf",
        workflow="TOE",
        reason="no_extractable_text",
        stage="quality_check",
        path="/tmp/bad.pdf",
    )

    report_path = write_report(str(tmp_path), [record], workflow="TOE")

    with open(report_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["workflow"] == "TOE"
    assert rows[0]["filename"] == "bad.pdf"
    assert rows[0]["reason"] == "no_extractable_text"
    assert rows[0]["stage"] == "quality_check"
    assert rows[0]["suggested_action"]


def test_settings_round_trip_in_config_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "_settings_dir", lambda: tmp_path)

    settings.remember_pdf_folder("/tmp/pdfs")
    settings.remember_save_path("/tmp/output/report.xlsx")
    settings.remember_include_client(False)

    data = settings.load_settings()
    assert data["last_pdf_folder"] == "/tmp/pdfs"
    assert data["last_save_directory"] == "/tmp/output"
    assert data["last_include_client"] is False
    assert data["recent_pdf_folders"] == ["/tmp/pdfs"]
