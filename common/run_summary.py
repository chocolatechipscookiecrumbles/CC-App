"""Shared workflow run summary models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


SUGGESTED_ACTIONS = {
    "not_pdf": "Choose a folder that contains NCAA report PDFs.",
    "name_not_found": "Confirm the reporting institution appears in the PDF text.",
    "no_extractable_text": "Confirm the PDF has selectable text instead of scanned images.",
    "section_not_found": "Confirm this PDF contains the expected NCAA report section.",
    "table_not_found": "Confirm this PDF contains the expected NCAA table.",
    "parse_error": "Review the PDF formatting or try regenerating the source PDF.",
    "empty_result": "Confirm the expected values are present in the report.",
    "user_excluded": "No action needed; this file was skipped by user choice.",
    "cancelled": "Run the workflow again when ready.",
}


@dataclass
class SkippedFileRecord:
    filename: str
    path: str = ""
    institution_name: str | None = None
    workflow: str = "Report"
    reason: str = "empty_result"
    stage: str = "processing"
    suggested_action: str | None = None
    exception_message: str | None = None

    def __post_init__(self):
        if self.suggested_action is None:
            self.suggested_action = SUGGESTED_ACTIONS.get(
                self.reason,
                "Review this file manually.",
            )

    @classmethod
    def from_item(cls, item: object, workflow: str = "Report") -> "SkippedFileRecord":
        if isinstance(item, cls):
            return item
        return cls(filename=str(item), workflow=workflow)


@dataclass
class WorkflowRunSummary:
    workflow: str
    folder_path: str
    output_path: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    pdfs_found: int = 0
    processed_count: int = 0
    skipped_files: list[SkippedFileRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_files)

    def add_processed(self, count: int = 1) -> None:
        self.processed_count += count

    def add_skipped(
        self,
        filename: str,
        *,
        path: str = "",
        institution_name: str | None = None,
        reason: str = "empty_result",
        stage: str = "processing",
        suggested_action: str | None = None,
        exception_message: str | None = None,
    ) -> SkippedFileRecord:
        record = SkippedFileRecord(
            filename=filename,
            path=path,
            institution_name=institution_name,
            workflow=self.workflow,
            reason=reason,
            stage=stage,
            suggested_action=suggested_action,
            exception_message=exception_message,
        )
        self.skipped_files.append(record)
        return record

    def finish(self, *, output_path: str | None = None, cancelled: bool | None = None) -> None:
        if output_path:
            self.output_path = output_path
        if cancelled is not None:
            self.cancelled = cancelled
        self.finished_at = datetime.now()
        self.duration_seconds = (self.finished_at - self.started_at).total_seconds()

    def reason_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.skipped_files:
            counts[record.reason] = counts.get(record.reason, 0) + 1
        return counts
