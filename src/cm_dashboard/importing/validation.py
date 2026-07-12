"""Validation checks for source folders and imported data."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from cm_dashboard.importing.accepted_issues import (
    accepted_fingerprints_for,
    coverage_fingerprint,
)
from cm_dashboard.importing.filename import (
    DateBasis,
    Direction,
    ExportEntity,
    FileExtension,
    ParsedFilename,
)
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


DERIVED_VALIDATION_CODES = {
    "accepted_period_coverage_summary",
    "article_shipment_mismatch",
    "conflicting_shipment_event",
    "duplicate_article_source_overlap",
    "missing_period_coverage",
    "shipment_grouping_summary",
    "shipment_total_mismatch",
    "unmatched_article_order",
}


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


def validate_database(
    connection: sqlite3.Connection,
    *,
    accepted_fingerprints: frozenset[str] | None = None,
) -> tuple[ValidationIssue, ...]:
    if accepted_fingerprints is None:
        accepted_fingerprints = accepted_fingerprints_for(connection)
    issues: list[ValidationIssue] = []
    issues.extend(
        _filter_accepted_coverage(_database_coverage_issues(connection), accepted_fingerprints)
    )
    issues.extend(_unmatched_article_issues(connection))
    duplicate_issue = _duplicate_raw_article_summary_issue(connection)
    if duplicate_issue is not None:
        issues.append(duplicate_issue)
    issues.extend(_article_shipment_reconciliation_issues(connection))
    issues.extend(_shipment_total_issues(connection))
    issues.extend(_shipment_event_conflict_issues(connection))
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


def refresh_validation_issues(
    connection: sqlite3.Connection,
    issues: tuple[ValidationIssue, ...] | None = None,
) -> int:
    resolved_issues = issues if issues is not None else validate_database(connection)
    placeholders = ", ".join("?" for _ in DERIVED_VALIDATION_CODES)
    with connection:
        connection.execute(
            f"DELETE FROM import_issues WHERE code IN ({placeholders})",
            tuple(sorted(DERIVED_VALIDATION_CODES)),
        )
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
                for issue in resolved_issues
            ),
        )
    return len(resolved_issues)


def _filter_accepted_coverage(
    issues: tuple[ValidationIssue, ...],
    accepted_fingerprints: frozenset[str],
) -> tuple[ValidationIssue, ...]:
    if not accepted_fingerprints:
        return issues
    remaining: list[ValidationIssue] = []
    accepted_count = 0
    for issue in issues:
        fingerprint = coverage_fingerprint(issue)
        if fingerprint is not None and fingerprint in accepted_fingerprints:
            accepted_count += 1
            continue
        remaining.append(issue)
    if accepted_count:
        remaining.append(
            ValidationIssue(
                severity="info",
                code="accepted_period_coverage_summary",
                message=(
                    f"{accepted_count} known coverage gaps are acknowledged in "
                    "accepted_issues.json and hidden from this report"
                ),
            )
        )
    return tuple(remaining)


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


def _database_coverage_issues(connection: sqlite3.Connection) -> tuple[ValidationIssue, ...]:
    rows = connection.execute(
        """
        SELECT file_name, file_extension, direction, entity, date_basis,
               period_start, period_end
        FROM import_files
        WHERE import_status = 'imported'
        ORDER BY import_file_id
        """
    ).fetchall()
    metadata = [
        ParsedFilename(
            file_name=row["file_name"],
            file_extension=FileExtension(row["file_extension"]),
            direction=Direction(row["direction"]),
            entity=ExportEntity(row["entity"]),
            date_basis=DateBasis(row["date_basis"]),
            period_start=date.fromisoformat(row["period_start"]),
            period_end=date.fromisoformat(row["period_end"]),
        )
        for row in rows
    ]
    return _coverage_issues(metadata)


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


def _duplicate_raw_article_summary_issue(
    connection: sqlite3.Connection,
) -> ValidationIssue | None:
    row = connection.execute(
        """
        SELECT COUNT(*) AS overlap_count
        FROM (
            SELECT business_key
            FROM raw_article_rows
            WHERE business_key IS NOT NULL
            GROUP BY business_key
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()
    if not row or row["overlap_count"] == 0:
        return None
    return ValidationIssue(
        severity="info",
        code="duplicate_article_source_overlap",
        message=(
            f"{row['overlap_count']} article rows occur in parallel source exports and are "
            "counted once in normalized reports"
        ),
    )


def _article_shipment_reconciliation_issues(
    connection: sqlite3.Connection,
) -> tuple[ValidationIssue, ...]:
    rows = connection.execute(
        """
        SELECT
            article_lines.direction,
            article_lines.order_id,
            article_lines.date_basis,
            SUM(article_lines.quantity) AS line_quantity,
            ROUND(SUM(CAST(article_lines.total AS REAL)), 2) AS line_total,
            shipments.article_count,
            ROUND(CAST(shipments.merchandise_value AS REAL), 2) AS merchandise_value,
            MIN(article_lines.source_import_file_id) AS import_file_id
        FROM article_lines
        JOIN shipments ON shipments.shipment_id = article_lines.shipment_id
        GROUP BY article_lines.direction, article_lines.order_id, article_lines.date_basis
        HAVING
            (shipments.article_count IS NOT NULL AND line_quantity != shipments.article_count)
            OR (shipments.merchandise_value IS NOT NULL
                AND ABS(line_total - merchandise_value) > 0.01)
        ORDER BY article_lines.direction, article_lines.order_id, article_lines.date_basis
        """
    ).fetchall()
    return tuple(
        ValidationIssue(
            severity="warning",
            code="article_shipment_mismatch",
            message=(
                f"{row['direction']} order {row['order_id']} ({row['date_basis']}) has "
                f"article quantity/value {row['line_quantity']}/{row['line_total']} but "
                f"shipment values {row['article_count']}/{row['merchandise_value']}"
            ),
            import_file_id=row["import_file_id"],
        )
        for row in rows
    )


def _shipment_total_issues(connection: sqlite3.Connection) -> tuple[ValidationIssue, ...]:
    rows = connection.execute(
        """
        SELECT shipment_id, direction, order_id, merchandise_value, shipment_costs,
               trustee_service_fee, total_value
        FROM shipments
        WHERE total_value IS NOT NULL
          AND ABS(
              CAST(total_value AS REAL)
              - CAST(merchandise_value AS REAL)
              - CAST(shipment_costs AS REAL)
              - CASE WHEN direction = 'PURCHASED'
                     THEN COALESCE(CAST(trustee_service_fee AS REAL), 0)
                     ELSE 0 END
          ) > 0.01
        ORDER BY direction, order_id
        """
    ).fetchall()
    return tuple(
        ValidationIssue(
            severity="warning",
            code="shipment_total_mismatch",
            message=f"{row['direction']} order {row['order_id']} has inconsistent total value",
        )
        for row in rows
    )


def _shipment_event_conflict_issues(
    connection: sqlite3.Connection,
) -> tuple[ValidationIssue, ...]:
    rows = connection.execute(
        """
        SELECT shipments.direction, shipments.order_id, shipment_events.event_type,
               COUNT(DISTINCT shipment_events.event_datetime) AS value_count,
               MIN(shipment_events.source_import_file_id) AS import_file_id
        FROM shipment_events
        JOIN shipments USING (shipment_id)
        GROUP BY shipment_events.shipment_id, shipment_events.event_type
        HAVING COUNT(DISTINCT shipment_events.event_datetime) > 1
        ORDER BY shipments.direction, shipments.order_id, shipment_events.event_type
        """
    ).fetchall()
    return tuple(
        ValidationIssue(
            severity="warning",
            code="conflicting_shipment_event",
            message=(
                f"{row['direction']} order {row['order_id']} has {row['value_count']} "
                f"different {row['event_type']} timestamps"
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
