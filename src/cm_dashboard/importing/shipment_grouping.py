"""Resolve grouped rows in Cardmarket shipment exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cm_dashboard.importing.normalize import is_empty, normalize_identifier
from cm_dashboard.importing.readers import WorksheetData

LINE_DETAIL_COLUMNS = {"Description", "Product ID", "Localized Product Name"}


@dataclass(frozen=True)
class ResolvedShipmentRow:
    source_row_number: int
    values: dict[str, Any]
    inherited_values: dict[str, Any]
    order_id: str | None
    resolved_order_id: str | None
    is_header_row: bool


def resolve_shipment_groups(sheet: WorksheetData) -> tuple[ResolvedShipmentRow, ...]:
    if "OrderID" not in sheet.headers:
        raise ValueError("Shipment sheet is missing required OrderID column")

    current_order_id: str | None = None
    current_header_values: dict[str, Any] = {}
    resolved_rows: list[ResolvedShipmentRow] = []

    for row_index, row in enumerate(sheet.rows, start=2):
        values = dict(zip(sheet.headers, row, strict=True))
        order_id = normalize_identifier(values.get("OrderID"))
        is_header_row = order_id is not None

        if is_header_row:
            current_order_id = order_id
            current_header_values = values

        inherited_values = _inherit_header_values(values, current_header_values)
        resolved_rows.append(
            ResolvedShipmentRow(
                source_row_number=row_index,
                values=values,
                inherited_values=inherited_values,
                order_id=order_id,
                resolved_order_id=current_order_id,
                is_header_row=is_header_row,
            )
        )

    return tuple(resolved_rows)


def _inherit_header_values(values: dict[str, Any], header_values: dict[str, Any]) -> dict[str, Any]:
    inherited = dict(values)
    for column, header_value in header_values.items():
        if column in LINE_DETAIL_COLUMNS:
            continue
        if is_empty(inherited.get(column)) and not is_empty(header_value):
            inherited[column] = header_value
    return inherited
