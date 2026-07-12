"""Synthetic Cardmarket-shaped sources without private account data."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

from cm_dashboard.importing.filename import DateBasis, ParsedFilename, require_parsed_filename
from cm_dashboard.importing.schemas import schema_for


def write_article_source(
    path: Path,
    *,
    rows: Sequence[Mapping[str, str]] | None = None,
    overrides: Mapping[str, str] | None = None,
) -> Path:
    metadata = require_parsed_filename(path)
    date_column = (
        "Date of purchase"
        if metadata.date_basis == DateBasis.PURCHASEDATE
        else "Date of payment"
    )
    default_row = {
        "Shipment nr.": "order-1001",
        date_column: "2026-08-12 10:00:00",
        "Article": "Synthetic Card",
        "Product ID": "product-2001",
        "Localized Product Name": "Synthetic Card",
        "Expansion": "Synthetic Set",
        "Category": "Synthetic Category",
        "Amount": "1",
        "Article Value": "8.0",
        "Total": "8.0",
        "Currency": "EUR",
        "Comments": "fixture",
    }
    default_row.update(overrides or {})
    return _write_source(path, metadata, rows or (default_row,))


def write_shipment_source(
    path: Path,
    *,
    order_id: str = "order-1001",
    username: str = "synthetic-user",
    overrides: Mapping[str, str] | None = None,
) -> Path:
    metadata = require_parsed_filename(path)
    date_column = (
        "Date of Purchase"
        if metadata.date_basis == DateBasis.PURCHASEDATE
        else "Date of Payment"
    )
    fee_column = "Trustee service fee" if metadata.direction.value == "PURCHASED" else "Commission"
    header = {
        "OrderID": order_id,
        "Username": username,
        "Name": "Synthetic Person",
        "Street": "Example Street 1",
        "City": "Example City",
        "Country": "Germany",
        "Is Professional": "",
        "VAT Number": "",
        date_column: "2026-08-12 12:00:00",
        "Article Count": "1",
        "Merchandise Value": "8.0",
        "Shipment Costs": "1.5",
        fee_column: "0.0",
        "Total Value": "9.5",
        "Currency": "EUR",
        "Description": "1x Synthetic Card",
        "Product ID": "product-2001",
        "Localized Product Name": "Synthetic Card",
    }
    header.update(overrides or {})
    return _write_source(path, metadata, (header,))


def _write_source(
    path: Path,
    metadata: ParsedFilename,
    rows: Sequence[Mapping[str, str]],
) -> Path:
    if path.suffix.lower() != ".csv":
        raise ValueError(f"Synthetic sources are written as CSV; got {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=schema_for(metadata).columns,
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return path
