"""Persistence for import files and raw source rows."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from cm_dashboard.importing.deduplication import (
    article_business_keys,
    serialize_article_business_key,
)
from cm_dashboard.importing.filename import ParsedFilename
from cm_dashboard.importing.normalize import normalize_identifier
from cm_dashboard.importing.readers import WorksheetData
from cm_dashboard.importing.shipment_grouping import resolve_shipment_groups
from cm_dashboard.importing.version import NORMALIZATION_VERSION


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upsert_import_file(
    connection: sqlite3.Connection,
    *,
    path: str | Path,
    metadata: ParsedFilename,
    file_hash: str | None = None,
    sheet_name: str | None = None,
    row_count: int = 0,
    import_status: str = "pending",
    normalization_version: int = NORMALIZATION_VERSION,
) -> int:
    source_path = Path(path).resolve(strict=False)
    resolved_hash = file_hash or file_sha256(source_path)
    connection.execute(
        """
        INSERT INTO import_files (
            original_path, file_name, file_hash, file_extension, direction, entity,
            date_basis, period_start, period_end, sheet_name, import_status, row_count,
            normalization_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(original_path) DO UPDATE SET
            file_name = excluded.file_name,
            file_hash = excluded.file_hash,
            file_extension = excluded.file_extension,
            direction = excluded.direction,
            entity = excluded.entity,
            date_basis = excluded.date_basis,
            period_start = excluded.period_start,
            period_end = excluded.period_end,
            sheet_name = excluded.sheet_name,
            import_status = excluded.import_status,
            row_count = excluded.row_count,
            normalization_version = excluded.normalization_version,
            imported_at = NULL
        """,
        (
            str(source_path),
            metadata.file_name,
            resolved_hash,
            metadata.file_extension.value,
            metadata.direction.value,
            metadata.entity.value,
            metadata.date_basis.value,
            metadata.period_start.isoformat(),
            metadata.period_end.isoformat(),
            sheet_name,
            import_status,
            row_count,
            normalization_version,
        ),
    )
    row = connection.execute(
        "SELECT import_file_id FROM import_files WHERE original_path = ?",
        (str(source_path),),
    ).fetchone()
    return int(row["import_file_id"])


def store_raw_article_rows(
    connection: sqlite3.Connection,
    *,
    import_file_id: int,
    sheet: WorksheetData,
    metadata: ParsedFilename,
) -> int:
    rows = []
    business_keys = article_business_keys(sheet, metadata)
    for row_index, (row, key) in enumerate(zip(sheet.rows, business_keys, strict=True), start=2):
        row_values = dict(zip(sheet.headers, row, strict=True))
        rows.append(
            (
                import_file_id,
                row_index,
                normalize_identifier(row_values.get("Shipment nr.")),
                serialize_article_business_key(key),
                _json_dumps(row_values),
            )
        )

    connection.execute(
        "DELETE FROM raw_article_rows WHERE import_file_id = ?",
        (import_file_id,),
    )
    connection.executemany(
        """
        INSERT INTO raw_article_rows (
            import_file_id, source_row_number, order_id, business_key, raw_values_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def store_raw_shipment_rows(
    connection: sqlite3.Connection,
    *,
    import_file_id: int,
    sheet: WorksheetData,
) -> int:
    rows = []
    for row in resolve_shipment_groups(sheet):
        rows.append(
            (
                import_file_id,
                row.source_row_number,
                row.order_id,
                row.resolved_order_id,
                1 if row.is_header_row else 0,
                _json_dumps(row.values),
                _json_dumps(row.inherited_values),
            )
        )

    connection.execute(
        "DELETE FROM raw_shipment_rows WHERE import_file_id = ?",
        (import_file_id,),
    )
    connection.executemany(
        """
        INSERT INTO raw_shipment_rows (
            import_file_id, source_row_number, order_id, resolved_order_id,
            is_header_row, raw_values_json, inherited_values_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
