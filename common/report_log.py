"""Shared skipped-file report writing."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Iterable

from .run_summary import SkippedFileRecord


def write_report(folder_path: str, items: Iterable[object], workflow: str = "Report") -> str | None:
    records = [SkippedFileRecord.from_item(item, workflow=workflow) for item in list(items or [])]
    if not records:
        return None

    os.makedirs(folder_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_workflow = "".join(ch if ch.isalnum() else "_" for ch in workflow).strip("_").lower()
    filename = f"skipped_{safe_workflow}_{timestamp}.csv"
    full_path = os.path.join(folder_path, filename)

    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "workflow",
                "filename",
                "institution_name",
                "reason",
                "stage",
                "suggested_action",
                "exception_message",
                "path",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "workflow": record.workflow,
                    "filename": record.filename,
                    "institution_name": record.institution_name or "",
                    "reason": record.reason,
                    "stage": record.stage,
                    "suggested_action": record.suggested_action or "",
                    "exception_message": record.exception_message or "",
                    "path": record.path,
                }
            )

    return full_path
