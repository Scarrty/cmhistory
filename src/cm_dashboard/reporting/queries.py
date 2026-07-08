"""Read-only dashboard/reporting SQL queries."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ReportingFilters:
    start_date: str | date | None = None
    end_date: str | date | None = None
    direction: str | None = None
    date_basis: str | None = None
    order_id: str | None = None
    product_id: str | None = None
    product_text: str | None = None
    expansion: str | None = None
    category: str | None = None
    username: str | None = None
    country: str | None = None


def fetch_article_lines(
    connection: sqlite3.Connection,
    filters: ReportingFilters | None = None,
    *,
    limit: int = 500,
) -> list[dict[str, Any]]:
    filters = filters or ReportingFilters()
    where, params = _article_where(filters)
    params.append(limit)
    rows = connection.execute(
        f"""
        SELECT
            article_lines.article_line_id,
            article_lines.order_id,
            article_lines.direction,
            article_lines.date_basis,
            article_lines.event_datetime,
            article_lines.article_name_snapshot,
            article_lines.product_id,
            article_lines.localized_product_name,
            article_lines.expansion_name_snapshot,
            article_lines.category_name_snapshot,
            article_lines.quantity,
            article_lines.article_value,
            article_lines.total,
            article_lines.currency,
            article_lines.comments,
            shipments.username,
            shipments.country
        FROM article_lines
        LEFT JOIN shipments ON shipments.shipment_id = article_lines.shipment_id
        {where}
        ORDER BY article_lines.event_datetime DESC, article_lines.article_line_id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [_row_dict(row) for row in rows]


def fetch_shipments(
    connection: sqlite3.Connection,
    filters: ReportingFilters | None = None,
    *,
    limit: int = 500,
) -> list[dict[str, Any]]:
    filters = filters or ReportingFilters()
    where, params = _shipment_where(filters)
    params.append(limit)
    rows = connection.execute(
        f"""
        SELECT DISTINCT
            shipments.shipment_id,
            shipments.order_id,
            shipments.direction,
            shipments.username,
            shipments.country,
            shipments.article_count,
            shipments.merchandise_value,
            shipments.shipment_costs,
            shipments.trustee_service_fee,
            shipments.commission,
            shipments.total_value,
            shipments.currency
        FROM shipments
        LEFT JOIN shipment_events ON shipment_events.shipment_id = shipments.shipment_id
        {where}
        ORDER BY shipments.order_id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [_row_dict(row) for row in rows]


def period_totals(
    connection: sqlite3.Connection,
    filters: ReportingFilters | None = None,
) -> dict[str, Any]:
    filters = filters or ReportingFilters()
    where, params = _article_where(filters)
    row = connection.execute(
        f"""
        SELECT
            COUNT(*) AS article_line_count,
            COUNT(DISTINCT article_lines.order_id) AS shipment_count,
            COALESCE(SUM(CASE WHEN article_lines.direction = 'PURCHASED'
                THEN CAST(article_lines.total AS REAL) ELSE 0 END), 0) AS purchase_total,
            COALESCE(SUM(CASE WHEN article_lines.direction = 'SOLD'
                THEN CAST(article_lines.total AS REAL) ELSE 0 END), 0) AS sales_total,
            COALESCE(SUM(CAST(article_lines.total AS REAL)), 0) AS combined_total
        FROM article_lines
        LEFT JOIN shipments ON shipments.shipment_id = article_lines.shipment_id
        {where}
        """,
        params,
    ).fetchone()
    return _row_dict(row)


def monthly_totals(
    connection: sqlite3.Connection,
    filters: ReportingFilters | None = None,
) -> list[dict[str, Any]]:
    filters = filters or ReportingFilters()
    where, params = _article_where(filters)
    rows = connection.execute(
        f"""
        SELECT
            SUBSTR(article_lines.event_datetime, 1, 7) AS month,
            article_lines.direction,
            COUNT(*) AS article_line_count,
            COUNT(DISTINCT article_lines.order_id) AS shipment_count,
            COALESCE(SUM(CAST(article_lines.total AS REAL)), 0) AS total
        FROM article_lines
        LEFT JOIN shipments ON shipments.shipment_id = article_lines.shipment_id
        {where}
        GROUP BY month, article_lines.direction
        ORDER BY month, article_lines.direction
        """,
        params,
    ).fetchall()
    return [_row_dict(row) for row in rows]


def period_report_rows(
    connection: sqlite3.Connection,
    filters: ReportingFilters | None = None,
) -> list[dict[str, Any]]:
    filters = filters or ReportingFilters()
    totals = period_totals(connection, filters)
    rows = [
        {
            "section": "period",
            "month": "",
            "direction": "ALL",
            "article_line_count": totals["article_line_count"],
            "shipment_count": totals["shipment_count"],
            "purchase_total": totals["purchase_total"],
            "sales_total": totals["sales_total"],
            "total": totals["combined_total"],
        }
    ]
    rows.extend(
        {
            "section": "monthly",
            "month": row["month"],
            "direction": row["direction"],
            "article_line_count": row["article_line_count"],
            "shipment_count": row["shipment_count"],
            "purchase_total": "",
            "sales_total": "",
            "total": row["total"],
        }
        for row in monthly_totals(connection, filters)
    )
    return rows


def _article_where(filters: ReportingFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    _add_common_article_filters(clauses, params, filters)
    return _where_sql(clauses), params


def _shipment_where(filters: ReportingFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if filters.direction:
        clauses.append("shipments.direction = ?")
        params.append(filters.direction)
    if filters.date_basis:
        clauses.append("shipment_events.event_type = ?")
        params.append(filters.date_basis)
    if filters.start_date:
        clauses.append("shipment_events.event_datetime >= ?")
        params.append(_start_datetime(filters.start_date))
    if filters.end_date:
        clauses.append("shipment_events.event_datetime <= ?")
        params.append(_end_datetime(filters.end_date))
    if filters.order_id:
        clauses.append("shipments.order_id = ?")
        params.append(filters.order_id)
    if filters.username:
        clauses.append("shipments.username LIKE ?")
        params.append(f"%{filters.username}%")
    if filters.country:
        clauses.append("shipments.country = ?")
        params.append(filters.country)
    return _where_sql(clauses), params


def _add_common_article_filters(
    clauses: list[str], params: list[Any], filters: ReportingFilters
) -> None:
    if filters.direction:
        clauses.append("article_lines.direction = ?")
        params.append(filters.direction)
    if filters.date_basis:
        clauses.append("article_lines.date_basis = ?")
        params.append(filters.date_basis)
    if filters.start_date:
        clauses.append("article_lines.event_datetime >= ?")
        params.append(_start_datetime(filters.start_date))
    if filters.end_date:
        clauses.append("article_lines.event_datetime <= ?")
        params.append(_end_datetime(filters.end_date))
    if filters.order_id:
        clauses.append("article_lines.order_id = ?")
        params.append(filters.order_id)
    if filters.product_id:
        clauses.append("article_lines.product_id = ?")
        params.append(filters.product_id)
    if filters.product_text:
        clauses.append(
            """
            (
                article_lines.article_name_snapshot LIKE ?
                OR article_lines.localized_product_name LIKE ?
                OR article_lines.product_id = ?
            )
            """
        )
        like_value = f"%{filters.product_text}%"
        params.extend([like_value, like_value, filters.product_text])
    if filters.expansion:
        clauses.append("article_lines.expansion_name_snapshot = ?")
        params.append(filters.expansion)
    if filters.category:
        clauses.append("article_lines.category_name_snapshot = ?")
        params.append(filters.category)
    if filters.username:
        clauses.append("shipments.username LIKE ?")
        params.append(f"%{filters.username}%")
    if filters.country:
        clauses.append("shipments.country = ?")
        params.append(filters.country)


def _where_sql(clauses: list[str]) -> str:
    return "WHERE " + " AND ".join(clauses) if clauses else ""


def _start_datetime(value: str | date) -> str:
    text = value.isoformat() if isinstance(value, date) else str(value)
    return f"{text} 00:00:00" if len(text) == 10 else text


def _end_datetime(value: str | date) -> str:
    text = value.isoformat() if isinstance(value, date) else str(value)
    return f"{text} 23:59:59" if len(text) == 10 else text


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)
