"""Shared PDF folder scanning and institution-name manifest helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List

from .pdf_names import extract_reporting_institution, fallback_institution_from_filename


@dataclass(frozen=True)
class PDFRecord:
    path: str
    filename: str
    institution_name: str
    name_source: str


def build_pdf_manifest(folder_path: str) -> List[PDFRecord]:
    """Scan a folder once and return sorted PDF records with institution names."""
    records: List[PDFRecord] = []

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(folder_path, filename)
        institution_name = extract_reporting_institution(pdf_path)
        name_source = "pdf"

        if not institution_name:
            institution_name = fallback_institution_from_filename(filename)
            name_source = "filename"

        records.append(
            PDFRecord(
                path=pdf_path,
                filename=filename,
                institution_name=institution_name,
                name_source=name_source,
            )
        )

    return sorted(records, key=lambda record: record.institution_name.lower())


def manifest_institution_names(manifest: Iterable[PDFRecord]) -> List[str]:
    return [record.institution_name for record in manifest]

