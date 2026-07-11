"""Normalize article exports into product and article-line tables."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from cm_dashboard.importing.deduplication import (
    ArticleBusinessKey,
    article_business_keys,
    serialize_article_business_key,
)
from cm_dashboard.importing.filename import DateBasis, ParsedFilename
from cm_dashboard.importing.normalize import (
    normalize_currency,
    normalize_datetime,
    normalize_decimal,
    normalize_identifier,
    normalize_int,
    normalize_text,
)
from cm_dashboard.importing.readers import WorksheetData


def import_article_sheet(
    connection: sqlite3.Connection,
    *,
    import_file_id: int,
    sheet: WorksheetData,
    metadata: ParsedFilename,
) -> int:
    imported_count = 0
    business_keys = article_business_keys(sheet, metadata)
    for source_row_number, (row, business_key) in enumerate(
        zip(sheet.rows, business_keys, strict=True), start=2
    ):
        row_values = dict(zip(sheet.headers, row, strict=True))
        _import_article_row(
            connection,
            import_file_id=import_file_id,
            source_row_number=source_row_number,
            row=row_values,
            metadata=metadata,
            business_key=business_key,
        )
        imported_count += 1
    return imported_count


@dataclass(frozen=True)
class ArticleShipmentLinkResult:
    linked_count: int
    unmatched_order_ids: tuple[str, ...]


def link_article_lines_to_shipments(
    connection: sqlite3.Connection,
    *,
    record_issues: bool = True,
) -> ArticleShipmentLinkResult:
    cursor = connection.execute(
        """
        UPDATE article_lines
        SET shipment_id = (
            SELECT shipments.shipment_id
            FROM shipments
                WHERE shipments.order_id = article_lines.order_id
                  AND shipments.direction = article_lines.direction
        )
        WHERE shipment_id IS NULL
          AND EXISTS (
            SELECT 1
            FROM shipments
                WHERE shipments.order_id = article_lines.order_id
                  AND shipments.direction = article_lines.direction
          )
        """
    )
    unmatched_rows = connection.execute(
        """
        SELECT direction, order_id, MIN(source_import_file_id) AS import_file_id
        FROM article_lines
        WHERE shipment_id IS NULL
        GROUP BY direction, order_id
        ORDER BY direction, order_id
        """
    ).fetchall()
    if record_issues:
        connection.executemany(
            """
            INSERT INTO import_issues (
                import_file_id, severity, code, message
            ) VALUES (?, 'warning', 'unmatched_article_order', ?)
            """,
            (
                (
                    row["import_file_id"],
                    f"{row['direction']} article order {row['order_id']} has no matching shipment",
                )
                for row in unmatched_rows
            ),
        )

    return ArticleShipmentLinkResult(
        linked_count=cursor.rowcount,
        unmatched_order_ids=tuple(row["order_id"] for row in unmatched_rows),
    )


def _import_article_row(
    connection: sqlite3.Connection,
    *,
    import_file_id: int,
    source_row_number: int,
    row: dict[str, Any],
    metadata: ParsedFilename,
    business_key: ArticleBusinessKey,
) -> None:
    order_id = _required_identifier(row.get("Shipment nr."), "Shipment nr.")
    product_id = _required_identifier(row.get("Product ID"), "Product ID")
    localized_name = normalize_text(row.get("Localized Product Name"))
    expansion_name = normalize_text(row.get("Expansion"))
    category_name = normalize_text(row.get("Category"))
    date_column = _article_date_column(metadata.date_basis)
    event_datetime = _required_datetime(row.get(date_column), date_column)
    business_key_value = serialize_article_business_key(business_key)

    connection.execute("INSERT OR IGNORE INTO products (product_id) VALUES (?)", (product_id,))
    if localized_name:
        connection.execute(
            """
            INSERT OR IGNORE INTO product_labels (product_id, label, source_import_file_id)
            VALUES (?, ?, ?)
            """,
            (product_id, localized_name, import_file_id),
        )

    expansion_id = _get_or_create_named_row(connection, "expansions", expansion_name)
    category_id = _get_or_create_named_row(connection, "categories", category_name)
    shipment_id = _shipment_id_for_order(connection, order_id, metadata.direction.value)

    connection.execute(
        """
        INSERT INTO article_lines (
            shipment_id, order_id, direction, date_basis, event_datetime,
            article_name_snapshot, product_id, localized_product_name,
            expansion_id, expansion_name_snapshot, category_id, category_name_snapshot,
            quantity, article_value, total, currency, comments,
            source_import_file_id, source_row_number, business_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(business_key) DO UPDATE SET
            shipment_id = excluded.shipment_id,
            source_import_file_id = excluded.source_import_file_id,
            source_row_number = excluded.source_row_number
        """,
        (
            shipment_id,
            order_id,
            metadata.direction.value,
            metadata.date_basis.value,
            event_datetime.isoformat(sep=" "),
            _required_text(row.get("Article"), "Article"),
            product_id,
            localized_name,
            expansion_id,
            expansion_name,
            category_id,
            category_name,
            _required_int(row.get("Amount"), "Amount"),
            str(_required_decimal(row.get("Article Value"), "Article Value")),
            str(_required_decimal(row.get("Total"), "Total")),
            _required_currency(row.get("Currency"), "Currency"),
            normalize_text(row.get("Comments")),
            import_file_id,
            source_row_number,
            business_key_value,
        ),
    )


def _get_or_create_named_row(
    connection: sqlite3.Connection, table_name: str, name: str | None
) -> int | None:
    if not name:
        return None
    connection.execute(f"INSERT OR IGNORE INTO {table_name} (name) VALUES (?)", (name,))
    row = connection.execute(f"SELECT rowid FROM {table_name} WHERE name = ?", (name,)).fetchone()
    return int(row[0])


def _shipment_id_for_order(
    connection: sqlite3.Connection, order_id: str, direction: str
) -> int | None:
    row = connection.execute(
        "SELECT shipment_id FROM shipments WHERE direction = ? AND order_id = ?",
        (direction, order_id),
    ).fetchone()
    return int(row["shipment_id"]) if row else None


def _article_date_column(date_basis: DateBasis) -> str:
    return "Date of purchase" if date_basis == DateBasis.PURCHASEDATE else "Date of payment"


def _required_identifier(value: Any, column: str) -> str:
    normalized = normalize_identifier(value)
    if normalized is None:
        raise ValueError(f"Missing required identifier column: {column}")
    return normalized


def _required_text(value: Any, column: str) -> str:
    normalized = normalize_text(value)
    if normalized is None:
        raise ValueError(f"Missing required text column: {column}")
    return normalized


def _required_int(value: Any, column: str) -> int:
    normalized = normalize_int(value)
    if normalized is None:
        raise ValueError(f"Missing required integer column: {column}")
    return normalized


def _required_decimal(value: Any, column: str) -> Decimal:
    normalized = normalize_decimal(value)
    if normalized is None:
        raise ValueError(f"Missing required decimal column: {column}")
    return normalized


def _required_datetime(value: Any, column: str) -> datetime:
    normalized = normalize_datetime(value)
    if normalized is None:
        raise ValueError(f"Missing required datetime column: {column}")
    return normalized


def _required_currency(value: Any, column: str) -> str:
    normalized = normalize_currency(value)
    if normalized is None:
        raise ValueError(f"Missing required currency column: {column}")
    return normalized


def source_file_name(sheet: WorksheetData) -> str:
    return Path(sheet.path).name
