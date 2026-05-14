"""Shared PDF institution-name extraction helpers."""

from __future__ import annotations

import os
import re
from typing import Optional


REPORTING_INSTITUTION_RE = re.compile(
    r"Reporting\s*Institution[:\-]?\s*"
    r"([A-Za-z0-9&.,'\-() ]+?)"
    r"(?=\s+(?:"
    r"(?:Reporting|Fiscal|Academic|Report)\s+[A-Z][A-Za-z]*(?:\s*\(.*?\))?\s*[:\-]"
    r"|Reporting\s*Year"
    r"|Fiscal\s*Year"
    r"|Academic\s*Year"
    r"|Report\s*Date"
    r"|Report\s*Period"
    r"))",
    re.IGNORECASE,
)

FY_SUFFIX_RE = re.compile(r",\s*FY\d{2,4}", re.IGNORECASE)


def fallback_institution_from_filename(filename: str) -> str:
    """Return the existing filename-based institution fallback."""
    institution = os.path.splitext(os.path.basename(filename))[0]
    return FY_SUFFIX_RE.sub("", institution).strip()


def _normalize_institution(institution: str) -> str:
    institution = institution.strip()
    institution = re.sub(r"\b(Reporting|Report|Year|FY|Fiscal|Academic)\b.*$", "", institution).strip()
    institution = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", institution)
    return re.sub(r"\s{2,}", " ", institution).strip()


def _match_reporting_institution(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    normalized_text = re.sub(r"\s+", " ", text.strip())
    match = REPORTING_INSTITUTION_RE.search(normalized_text)

    if not match:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "ReportingInstitution" in line.replace(" ", ""):
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                combined = line + " " + next_line
                match = REPORTING_INSTITUTION_RE.search(combined)
                if match:
                    break

    if not match:
        return None

    return _normalize_institution(match.group(1))


def extract_reporting_institution(
    pdf_path: str,
    first_page_text: Optional[str] = None,
    second_page_text: Optional[str] = None,
) -> Optional[str]:
    """
    Extract the reporting institution from a PDF.

    Callers can pass already-extracted first/second page text to avoid reopening
    a PDF when text has been cached by a manifest or parser.
    """
    try:
        if first_page_text is None and second_page_text is None:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                first_page_text = pdf.pages[0].extract_text() if len(pdf.pages) >= 1 else ""
                second_page_text = pdf.pages[1].extract_text() if len(pdf.pages) >= 2 else ""

        return _match_reporting_institution(first_page_text) or _match_reporting_institution(second_page_text)
    except Exception:
        return None
