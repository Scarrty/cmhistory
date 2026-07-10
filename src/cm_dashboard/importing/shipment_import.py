"""Normalize shipment exports into shipment and event tables."""

from __future__ import annotations

import sqlite3
from typing import Any

from cm_dashboard.importing.article_import import link_article_lines_to_shipments
from cm_dashboard.importing.filename import DateBasis, Direction, ParsedFilename
from cm_dashboard.importing.normalize import (
    normalize_bool,
    normalize_currency,
    normalize_datetime,
    normalize_decimal,
    normalize_identifier,
    normalize_int,
    normalize_text,
)
from cm_dashboard.importing.readers import WorksheetData
from cm_dashboard.importing.shipment_grouping import resolve_shipment_groups


def import_shipment_sheet(
    connection: sqlite3.Connection,
    *,
    import_file_id: int,
    sheet: WorksheetData,
    metadata: ParsedFilename,
    link_articles: bool = True,
) -> int:
    imported_count = 0
    for row in resolve_shipment_groups(sheet):
        if not row.is_header_row:
            continue
        _import_shipment_header(
            connection,
            import_file_id=import_file_id,
            source_row_number=row.source_row_number,
            values=row.inherited_values,
            metadata=metadata,
        )
        imported_count += 1
    if link_articles:
        link_article_lines_to_shipments(connection, record_issues=False)
    return imported_count


def _import_shipment_header(
    connection: sqlite3.Connection,
    *,
    import_file_id: int,
    source_row_number: int,
    values: dict[str, Any],
    metadata: ParsedFilename,
) -> None:
    order_id = _required_identifier(values.get("OrderID"), "OrderID")
    fee_values = _fee_values(values, metadata.direction)
    connection.execute(
        """
        INSERT INTO shipments (
            order_id, direction, username, counterparty_name, street, city, country,
            is_professional, vat_id_present, article_count, merchandise_value,
            shipment_costs, trustee_service_fee, commission, total_value, currency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(direction, order_id) DO UPDATE SET
            username = excluded.username,
            counterparty_name = excluded.counterparty_name,
            street = excluded.street,
            city = excluded.city,
            country = excluded.country,
            is_professional = excluded.is_professional,
            vat_id_present = excluded.vat_id_present,
            article_count = excluded.article_count,
            merchandise_value = excluded.merchandise_value,
            shipment_costs = excluded.shipment_costs,
            trustee_service_fee = excluded.trustee_service_fee,
            commission = excluded.commission,
            total_value = excluded.total_value,
            currency = excluded.currency
        """,
        (
            order_id,
            metadata.direction.value,
            normalize_text(values.get("Username")),
            normalize_text(values.get("Name")),
            normalize_text(values.get("Street")),
            normalize_text(values.get("City")),
            normalize_text(values.get("Country")),
            _bool_to_int(normalize_bool(values.get("Is Professional"))),
            1 if normalize_text(values.get("VAT Number")) else 0,
            normalize_int(values.get("Article Count")),
            _decimal_to_text(values.get("Merchandise Value")),
            _decimal_to_text(values.get("Shipment Costs")),
            fee_values["trustee_service_fee"],
            fee_values["commission"],
            _decimal_to_text(values.get("Total Value")),
            normalize_currency(values.get("Currency")),
        ),
    )
    shipment_id = connection.execute(
        "SELECT shipment_id FROM shipments WHERE direction = ? AND order_id = ?",
        (metadata.direction.value, order_id),
    ).fetchone()["shipment_id"]
    event_datetime = normalize_datetime(values.get(_shipment_date_column(metadata.date_basis)))
    if event_datetime is None:
        connection.execute(
            """
            INSERT INTO import_issues (
                import_file_id, severity, code, message, source_row_number
            ) VALUES (?, 'warning', 'missing_shipment_event_date', ?, ?)
            """,
            (
                import_file_id,
                f"Shipment {order_id} has no {metadata.date_basis.value} event date",
                source_row_number,
            ),
        )
        return
    connection.execute(
        """
        INSERT OR IGNORE INTO shipment_events (
            shipment_id, event_type, event_datetime, source_import_file_id
        ) VALUES (?, ?, ?, ?)
        """,
        (
            shipment_id,
            metadata.date_basis.value,
            event_datetime.isoformat(sep=" "),
            import_file_id,
        ),
    )


def _fee_values(values: dict[str, Any], direction: Direction) -> dict[str, str | None]:
    if direction == Direction.PURCHASED:
        return {
            "trustee_service_fee": _decimal_to_text(values.get("Trustee service fee")),
            "commission": None,
        }
    return {
        "trustee_service_fee": None,
        "commission": _decimal_to_text(values.get("Commission")),
    }


def _shipment_date_column(date_basis: DateBasis) -> str:
    return "Date of Purchase" if date_basis == DateBasis.PURCHASEDATE else "Date of Payment"


def _required_identifier(value: Any, column: str) -> str:
    normalized = normalize_identifier(value)
    if normalized is None:
        raise ValueError(f"Missing required identifier column: {column}")
    return normalized


def _decimal_to_text(value: Any) -> str | None:
    normalized = normalize_decimal(value)
    return str(normalized) if normalized is not None else None


def _bool_to_int(value: bool | None) -> int | None:
    return None if value is None else int(value)
