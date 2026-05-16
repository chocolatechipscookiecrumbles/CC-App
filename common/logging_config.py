"""Structured per-run logging helpers."""

from __future__ import annotations

import logging
import traceback
from datetime import datetime
from pathlib import Path

from . import settings


def _safe_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()
    return safe or "workflow"


def start_run_log(summary) -> logging.Logger:
    log_dir = settings.logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"{timestamp}_{_safe_name(summary.workflow)}.log"
    logger = logging.getLogger(f"programlauncher.run.{id(summary)}")
    logger.setLevel(logging.DEBUG if settings.load_settings().get("verbose_logging") else logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

    summary.extra["log_path"] = str(log_path)
    logger.info("Started workflow=%s folder=%s", summary.workflow, summary.folder_path)
    logger.info("Run options=%s", summary.extra)
    return logger


def get_run_logger(summary) -> logging.Logger:
    return logging.getLogger(f"programlauncher.run.{id(summary)}")


def log_exception(summary, exc: BaseException) -> None:
    logger = get_run_logger(summary)
    logger.error("Workflow exception: %s", exc)
    logger.error("Traceback:\n%s", traceback.format_exc())


def log_summary(summary) -> None:
    logger = get_run_logger(summary)
    if not logger.handlers:
        return

    logger.info("Finished workflow=%s cancelled=%s", summary.workflow, summary.cancelled)
    logger.info("PDFs found=%s processed=%s skipped=%s", summary.pdfs_found, summary.processed_count, summary.skipped_count)
    logger.info("Output path=%s duration_seconds=%s", summary.output_path, summary.duration_seconds)
    logger.info("Skipped reason counts=%s", summary.reason_counts())
    for record in summary.skipped_files:
        logger.info(
            "Skipped file=%s institution=%s reason=%s stage=%s exception=%s",
            record.filename,
            record.institution_name,
            record.reason,
            record.stage,
            record.exception_message,
        )

    for handler in list(logger.handlers):
        handler.flush()
