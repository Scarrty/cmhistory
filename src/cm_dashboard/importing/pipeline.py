"""End-to-end import orchestration."""

from __future__ import annotations

import os
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from cm_dashboard.db import create_database
from cm_dashboard.importing.article_import import (
    import_article_sheet,
    link_article_lines_to_shipments,
)
from cm_dashboard.importing.filename import ExportEntity, require_parsed_filename
from cm_dashboard.importing.raw_store import (
    file_sha256,
    store_raw_article_rows,
    store_raw_shipment_rows,
    upsert_import_file,
)
from cm_dashboard.importing.readers import read_spreadsheet
from cm_dashboard.importing.schemas import validate_headers
from cm_dashboard.importing.shipment_import import import_shipment_sheet
from cm_dashboard.importing.source_scan import SourceFile, scan_source_files
from cm_dashboard.importing.validation import refresh_validation_issues
from cm_dashboard.importing.version import NORMALIZATION_VERSION


class ImportPipelineError(RuntimeError):
    """Base error for safe import orchestration failures."""


class DatabaseRebuildRequiredError(ImportPipelineError):
    """Raised when stored facts use an older normalization algorithm."""


class SourceFileChangedError(ImportPipelineError):
    """Raised when an imported path now contains different source bytes."""


class ImportBatchError(ImportPipelineError):
    """Raised when an atomic database rebuild contains failed source files."""

    def __init__(
        self,
        message: str,
        *,
        failed_results: tuple[ImportResult, ...] = (),
    ) -> None:
        super().__init__(message)
        self.failed_results = failed_results


@dataclass(frozen=True)
class ImportResult:
    import_file_id: int
    file_name: str
    entity: str
    raw_row_count: int
    normalized_row_count: int
    status: str = "imported"
    error_message: str | None = None


def import_source_file(
    connection: sqlite3.Connection,
    source_file: SourceFile,
    *,
    link_shipments: bool = True,
) -> ImportResult:
    _require_current_normalization_version(connection)
    source_hash = file_sha256(source_file.path)
    existing = _existing_import_file(connection, source_file.path)
    if existing is not None:
        if existing["file_hash"] == source_hash and existing["import_status"] in {
            "imported",
            "conflict",
        }:
            if existing["import_status"] == "conflict":
                _restore_unchanged_source_status(connection, existing["import_file_id"])
            return ImportResult(
                import_file_id=existing["import_file_id"],
                file_name=source_file.path.name,
                entity=source_file.metadata.entity.value,
                raw_row_count=existing["row_count"],
                normalized_row_count=0,
                status="skipped",
            )
        if existing["file_hash"] != source_hash and existing["import_status"] in {
            "imported",
            "conflict",
        }:
            _record_changed_source_issue(connection, existing["import_file_id"])
            raise SourceFileChangedError(
                f"Imported source changed at {source_file.path}; rebuild the database explicitly"
            )

    sheet = None
    savepoint_started = False
    try:
        sheet = read_spreadsheet(source_file.path)
        header_result = validate_headers(sheet.headers, source_file.metadata)
        if not header_result.is_compatible:
            messages = "; ".join(issue.message for issue in header_result.issues)
            raise ValueError(
                f"Incompatible source headers for {source_file.path.name}: {messages}"
            )

        connection.execute("SAVEPOINT import_source_file")
        savepoint_started = True
        import_file_id = upsert_import_file(
            connection,
            path=source_file.path,
            metadata=source_file.metadata,
            file_hash=source_hash,
            sheet_name=sheet.sheet_name,
            row_count=sheet.row_count,
            import_status="processing",
        )
        connection.execute(
            "DELETE FROM import_issues WHERE import_file_id = ?",
            (import_file_id,),
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
            raw_count = store_raw_shipment_rows(
                connection, import_file_id=import_file_id, sheet=sheet
            )
            normalized_count = import_shipment_sheet(
                connection,
                import_file_id=import_file_id,
                sheet=sheet,
                metadata=source_file.metadata,
                link_articles=link_shipments,
            )
        connection.execute(
            """
            UPDATE import_files
            SET import_status = 'imported', imported_at = CURRENT_TIMESTAMP,
                normalization_version = ?
            WHERE import_file_id = ?
            """,
            (NORMALIZATION_VERSION, import_file_id),
        )
        connection.execute("RELEASE SAVEPOINT import_source_file")
        savepoint_started = False
    except Exception as exc:
        if savepoint_started:
            connection.execute("ROLLBACK TO SAVEPOINT import_source_file")
            connection.execute("RELEASE SAVEPOINT import_source_file")
        _record_failed_import(
            connection,
            source_file,
            file_hash=source_hash,
            sheet_name=sheet.sheet_name if sheet is not None else None,
            row_count=sheet.row_count if sheet is not None else 0,
            error=exc,
        )
        raise

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


def import_source_folder(
    connection: sqlite3.Connection, source_path: str | Path
) -> tuple[ImportResult, ...]:
    _require_current_normalization_version(connection)
    report = scan_source_files(source_path)
    results: list[ImportResult] = []
    for source_file in report.files:
        try:
            results.append(import_source_file(connection, source_file, link_shipments=False))
        except DatabaseRebuildRequiredError:
            raise
        except Exception as exc:
            existing = _existing_import_file(connection, source_file.path)
            results.append(
                ImportResult(
                    import_file_id=existing["import_file_id"] if existing is not None else 0,
                    file_name=source_file.path.name,
                    entity=source_file.metadata.entity.value,
                    raw_row_count=0,
                    normalized_row_count=0,
                    status="failed",
                    error_message=f"{type(exc).__name__}: {exc}",
                )
            )
    with connection:
        link_article_lines_to_shipments(connection, record_issues=False)
    refresh_validation_issues(connection)
    return tuple(results)


def rebuild_database(
    source_path: str | Path,
    database_path: str | Path,
) -> tuple[ImportResult, ...]:
    target = Path(database_path).expanduser().resolve(strict=False)
    if str(database_path) == ":memory:":
        raise ValueError("Database rebuild requires a filesystem target")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.rebuild")
    connection: sqlite3.Connection | None = None
    try:
        connection = create_database(temporary)
        results = import_source_folder(connection, source_path)
        failed = [result for result in results if result.status == "failed"]
        if failed:
            raise ImportBatchError(
                f"Database rebuild aborted because {len(failed)} source files failed",
                failed_results=tuple(failed),
            )
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or foreign_key_errors:
            raise ImportBatchError("Database rebuild failed integrity verification")
        connection.close()
        connection = None
        os.replace(temporary, target)
        return results
    finally:
        if connection is not None:
            connection.close()
        if temporary.exists():
            temporary.unlink()


def database_requires_rebuild(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM import_files
        WHERE import_status = 'imported' AND normalization_version != ?
        LIMIT 1
        """,
        (NORMALIZATION_VERSION,),
    ).fetchone()
    return row is not None


def _require_current_normalization_version(connection: sqlite3.Connection) -> None:
    if database_requires_rebuild(connection):
        raise DatabaseRebuildRequiredError(
            "Database contains facts from an older normalization version; run the rebuild command"
        )


def _existing_import_file(
    connection: sqlite3.Connection, path: str | Path
) -> sqlite3.Row | None:
    source_path = str(Path(path).resolve(strict=False))
    return cast(
        sqlite3.Row | None,
        connection.execute(
            "SELECT * FROM import_files WHERE original_path = ?",
            (source_path,),
        ).fetchone(),
    )


def _record_changed_source_issue(connection: sqlite3.Connection, import_file_id: int) -> None:
    with connection:
        connection.execute(
            "UPDATE import_files SET import_status = 'conflict' WHERE import_file_id = ?",
            (import_file_id,),
        )
        connection.execute(
            "DELETE FROM import_issues WHERE import_file_id = ? AND code = 'source_file_changed'",
            (import_file_id,),
        )
        connection.execute(
            """
            INSERT INTO import_issues (import_file_id, severity, code, message)
            VALUES (?, 'error', 'source_file_changed',
                    'Source bytes changed at an already imported path; explicit rebuild required')
            """,
            (import_file_id,),
        )


def _restore_unchanged_source_status(connection: sqlite3.Connection, import_file_id: int) -> None:
    with connection:
        connection.execute(
            "UPDATE import_files SET import_status = 'imported' WHERE import_file_id = ?",
            (import_file_id,),
        )
        connection.execute(
            "DELETE FROM import_issues WHERE import_file_id = ? AND code = 'source_file_changed'",
            (import_file_id,),
        )


def _record_failed_import(
    connection: sqlite3.Connection,
    source_file: SourceFile,
    *,
    file_hash: str,
    sheet_name: str | None,
    row_count: int,
    error: Exception,
) -> None:
    with connection:
        import_file_id = upsert_import_file(
            connection,
            path=source_file.path,
            metadata=source_file.metadata,
            file_hash=file_hash,
            sheet_name=sheet_name,
            row_count=row_count,
            import_status="failed",
        )
        connection.execute(
            "DELETE FROM import_issues WHERE import_file_id = ? AND code = 'import_failed'",
            (import_file_id,),
        )
        connection.execute(
            """
            INSERT INTO import_issues (import_file_id, severity, code, message)
            VALUES (?, 'error', 'import_failed', ?)
            """,
            (import_file_id, f"{type(error).__name__}: {error}"[:1000]),
        )
