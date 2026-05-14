"""Shared skipped-file report writing."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable


def write_report(folder_path: str, items: Iterable[object], workflow: str = "Report") -> None:
    items = list(items or [])
    if not items:
        return

    os.makedirs(folder_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_workflow = "".join(ch if ch.isalnum() else "_" for ch in workflow).strip("_").lower()
    filename = f"report_{safe_workflow}_{timestamp}.txt"
    full_path = os.path.join(folder_path, filename)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(f"{workflow}\n")
        for item in items:
            f.write(str(item) + "\n")

