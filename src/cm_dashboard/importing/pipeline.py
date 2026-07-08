"""End-to-end import orchestration."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from cm_dashboard.importing.article_import import import_article_sheet
from cm_dashboard.importing.article_import import link_article_lines_to_shipments
from cm_dashboard.importing.filename import ExportEntity, require_parsed_filename
from cm_dashboard.importing.raw_store import (
    store_raw_article_rows,
    store_raw_shipment_rows,
    upsert_import_file,
)
from cm_dashboard.importing.readers import read_spreadsheet
from cm_dashboard.importing.schemas import validate_headers
from cm_dashboard.importing.shipment_import import import_shipment_sheet
from cm_dashboard.importing.source_scan import SourceFile, scan_source_files


@dataclass(frozen=True)
class ImportResult:
    import_file_id: int
    file_name: str
    entity: str
    raw_row_count: int
    normalized_row_count: int


def import_source_file(
    connection: sqlite3.Connection,
    source_file: SourceFile,
    *,
    link_shipments: bool = True,
) -> ImportResult:
    sheet = read_spreadsheet(source_file.path)
    header_result = validate_headers(sheet.headers, source_file.metadata)
    if not header_result.is_compatible:
        messages = "; ".join(issue.message for issue in header_result.issues)
        raise ValueError(f"Incompatible source headers for {source_file.path.name}: {messages}")

    import_file_id = upsert_import_file(
        connection,
        path=source_file.path,
        metadata=source_file.metadata,
        sheet_name=sheet.sheet_name,
        row_count=sheet.row_count,
        import_status="imported",
    )

    if source_file.metadata.entity == ExportEntity.ARTICLES:
        raw_count = store_raw_article_rows(
            connection,
            import_file_id=import_file_id,
            sheet=sheet,
            metadata=source_file.metadata,
        )
        normalized_count = import_article_sheet(
            connection,
            import_file_id=import_file_id,
            sheet=sheet,
            metadata=source_file.metadata,
        )
    else:
        raw_count = store_raw_shipment_rows(connection, import_file_id=import_file_id, sheet=sheet)
        normalized_count = import_shipment_sheet(
            connection,
            import_file_id=import_file_id,
            sheet=sheet,
            metadata=source_file.metadata,
            link_articles=link_shipments,
        )

    return ImportResult(
        import_file_id=import_file_id,
        file_name=source_file.path.name,
        entity=source_file.metadata.entity.value,
        raw_row_count=raw_count,
        normalized_row_count=normalized_count,
    )


def import_source_path(connection: sqlite3.Connection, path: str | Path) -> ImportResult:
    source_path = Path(path).resolve(strict=False)
    metadata = require_parsed_filename(source_path)
    return import_source_file(connection, SourceFile(path=source_path, metadata=metadata))


def import_source_folder(connection: sqlite3.Connection, source_path: str | Path) -> tuple[ImportResult, ...]:
    report = scan_source_files(source_path)
    results = tuple(
        import_source_file(connection, source_file, link_shipments=False)
        for source_file in report.files
    )
    link_article_lines_to_shipments(connection, record_issues=False)
    return results
