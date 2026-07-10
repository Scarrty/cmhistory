"""Validation checks for source folders and imported data."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from cm_dashboard.importing.filename import DateBasis, ParsedFilename
from cm_dashboard.importing.readers import read_spreadsheet
from cm_dashboard.importing.schemas import validate_headers
from cm_dashboard.importing.source_scan import scan_source_files


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    import_file_id: int | None = None
    source_row_number: int | None = None
    file_path: str | None = None
    direction: str | None = None
    entity: str | None = None
    date_basis: str | None = None
    period_start: date | None = None
    period_end: date | None = None


def validate_source_folder(
    source_path: str | Path, *, check_headers: bool = True
) -> tuple[ValidationIssue, ...]:
    report = scan_source_files(source_path)
    issues: list[ValidationIssue] = []
    for unknown in report.unknown_files:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="unknown_source_file",
                message=unknown.issue.message,
                file_path=str(unknown.path),
            )
        )

    if check_headers:
        for source_file in report.files:
            sheet = read_spreadsheet(source_file.path)
            issues.extend(
                _issues_for_headers(
                    sheet.headers,
                    source_file.metadata,
                    file_path=str(source_file.path),
                )
            )

    issues.extend(_coverage_issues([source_file.metadata for source_file in report.files]))
    return tuple(issues)


def validate_database(connection: sqlite3.Connection) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    issues.extend(_unmatched_article_issues(connection))
    issues.extend(_duplicate_raw_article_issues(connection))
    grouping_issue = _shipment_grouping_summary_issue(connection)
    if grouping_issue is not None:
        issues.append(grouping_issue)
    return tuple(issues)


def persist_validation_issues(
    connection: sqlite3.Connection,
    issues: tuple[ValidationIssue, ...],
) -> int:
    with connection:
        connection.executemany(
            """
            INSERT INTO import_issues (
                import_file_id, severity, code, message, source_row_number
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                (
                    issue.import_file_id,
                    issue.severity,
                    issue.code,
                    issue.message,
                    issue.source_row_number,
                )
                for issue in issues
            ),
        )
    return len(issues)


def _issues_for_headers(
    headers: tuple[str, ...],
    metadata: ParsedFilename,
    *,
    file_path: str | None = None,
) -> tuple[ValidationIssue, ...]:
    result = validate_headers(headers, metadata)
    return tuple(
        ValidationIssue(
            severity="warning",
            code=f"header_{issue.kind.value}",
            message=issue.message,
            file_path=file_path,
            direction=metadata.direction.value,
            entity=metadata.entity.value,
            date_basis=metadata.date_basis.value,
            period_start=metadata.period_start,
            period_end=metadata.period_end,
        )
        for issue in result.issues
    )


def _coverage_issues(metadata_items: list[ParsedFilename]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    periods_by_context: dict[tuple[str, str], dict[DateBasis, set[tuple[date, date]]]] = {}
    for metadata in metadata_items:
        context = (metadata.direction.value, metadata.entity.value)
        periods_by_context.setdefault(
            context,
            {DateBasis.PURCHASEDATE: set(), DateBasis.PAYMENTDATE: set()},
        )
        periods_by_context[context][metadata.date_basis].add(
            (metadata.period_start, metadata.period_end)
        )

    for (direction, entity), periods_by_basis in sorted(periods_by_context.items()):
        all_periods = (
            periods_by_basis[DateBasis.PURCHASEDATE]
            | periods_by_basis[DateBasis.PAYMENTDATE]
        )
        for period_start, period_end in sorted(all_periods):
            for date_basis in (DateBasis.PURCHASEDATE, DateBasis.PAYMENTDATE):
                if (period_start, period_end) in periods_by_basis[date_basis]:
                    continue
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="missing_period_coverage",
                        message=(
                            f"Missing {direction} {entity} {date_basis.value} "
                            f"{period_start.isoformat()}_{period_end.isoformat()}"
                        ),
                        direction=direction,
                        entity=entity,
                        date_basis=date_basis.value,
                        period_start=period_start,
                        period_end=period_end,
                    )
                )
    return tuple(issues)


def _unmatched_article_issues(connection: sqlite3.Connection) -> tuple[ValidationIssue, ...]:
    rows = connection.execute(
        """
        SELECT direction, order_id, MIN(source_import_file_id) AS import_file_id
        FROM article_lines
        WHERE shipment_id IS NULL
        GROUP BY direction, order_id
        ORDER BY direction, order_id
        """
    ).fetchall()
    return tuple(
        ValidationIssue(
            severity="warning",
            code="unmatched_article_order",
            message=(
                f"{row['direction']} article order {row['order_id']} has no matching shipment"
            ),
            import_file_id=row["import_file_id"],
        )
        for row in rows
    )


def _duplicate_raw_article_issues(connection: sqlite3.Connection) -> tuple[ValidationIssue, ...]:
    rows = connection.execute(
        """
        SELECT business_key, COUNT(*) AS duplicate_count, MIN(import_file_id) AS import_file_id
        FROM raw_article_rows
        WHERE business_key IS NOT NULL
        GROUP BY business_key
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC
        """
    ).fetchall()
    return tuple(
        ValidationIssue(
            severity="warning",
            code="duplicate_article_business_key",
            message=(
                f"Article business key occurs {row['duplicate_count']} times "
                "across raw exports"
            ),
            import_file_id=row["import_file_id"],
        )
        for row in rows
    )


def _shipment_grouping_summary_issue(connection: sqlite3.Connection) -> ValidationIssue | None:
    row = connection.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            SUM(CASE WHEN is_header_row = 1 THEN 1 ELSE 0 END) AS header_count,
            SUM(CASE WHEN is_header_row = 0 THEN 1 ELSE 0 END) AS continuation_count
        FROM raw_shipment_rows
        """
    ).fetchone()
    if not row or row["row_count"] == 0:
        return None
    return ValidationIssue(
        severity="info",
        code="shipment_grouping_summary",
        message=(
            f"Shipment raw rows: {row['row_count']}; headers: {row['header_count']}; "
            f"continuations: {row['continuation_count']}"
        ),
    )
