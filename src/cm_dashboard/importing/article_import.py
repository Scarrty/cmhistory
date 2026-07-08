"""Normalize article exports into product and article-line tables."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from cm_dashboard.importing.deduplication import article_business_key_string
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
    with connection:
        for source_row_number, row in enumerate(sheet.rows, start=2):
            row_values = dict(zip(sheet.headers, row, strict=True))
            _import_article_row(
                connection,
                import_file_id=import_file_id,
                source_row_number=source_row_number,
                row=row_values,
                metadata=metadata,
            )
            imported_count += 1
    return imported_count


def _import_article_row(
    connection: sqlite3.Connection,
    *,
    import_file_id: int,
    source_row_number: int,
    row: dict[str, Any],
    metadata: ParsedFilename,
) -> None:
    order_id = _required_identifier(row.get("Shipment nr."), "Shipment nr.")
    product_id = _required_identifier(row.get("Product ID"), "Product ID")
    localized_name = normalize_text(row.get("Localized Product Name"))
    expansion_name = normalize_text(row.get("Expansion"))
    category_name = normalize_text(row.get("Category"))
    date_column = _article_date_column(metadata.date_basis)
    event_datetime = _required_datetime(row.get(date_column), date_column)
    business_key = article_business_key_string(row, metadata)

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
    shipment_id = _shipment_id_for_order(connection, order_id)

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
            business_key,
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


def _shipment_id_for_order(connection: sqlite3.Connection, order_id: str) -> int | None:
    row = connection.execute(
        "SELECT shipment_id FROM shipments WHERE order_id = ?",
        (order_id,),
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


def _required_decimal(value: Any, column: str):
    normalized = normalize_decimal(value)
    if normalized is None:
        raise ValueError(f"Missing required decimal column: {column}")
    return normalized


def _required_datetime(value: Any, column: str):
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
