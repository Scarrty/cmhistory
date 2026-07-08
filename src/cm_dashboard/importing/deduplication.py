"""Business keys for duplicate export-row detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

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


@dataclass(frozen=True)
class ArticleBusinessKey:
    order_id: str
    event_minute: datetime
    article: str
    product_id: str
    localized_product_name: str
    expansion: str
    category: str
    quantity: int
    article_value: Decimal
    total: Decimal
    currency: str
    comments: str


def article_business_keys(
    sheet: WorksheetData, metadata: ParsedFilename
) -> tuple[ArticleBusinessKey, ...]:
    return tuple(article_business_key(dict(zip(sheet.headers, row, strict=True)), metadata) for row in sheet.rows)


def article_business_key(
    row: Mapping[str, Any],
    metadata: ParsedFilename,
) -> ArticleBusinessKey:
    date_column = _article_date_column(metadata.date_basis)
    event_datetime = _required_datetime(row.get(date_column), date_column)
    return ArticleBusinessKey(
        order_id=_required_identifier(row.get("Shipment nr."), "Shipment nr."),
        event_minute=event_datetime.replace(second=0, microsecond=0),
        article=_required_text(row.get("Article"), "Article"),
        product_id=_required_identifier(row.get("Product ID"), "Product ID"),
        localized_product_name=_optional_text(row.get("Localized Product Name")),
        expansion=_optional_text(row.get("Expansion")),
        category=_optional_text(row.get("Category")),
        quantity=_required_int(row.get("Amount"), "Amount"),
        article_value=_required_decimal(row.get("Article Value"), "Article Value"),
        total=_required_decimal(row.get("Total"), "Total"),
        currency=_required_currency(row.get("Currency"), "Currency"),
        comments=_optional_text(row.get("Comments")),
    )


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


def _optional_text(value: Any) -> str:
    return normalize_text(value) or ""


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
