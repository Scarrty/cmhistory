import pytest

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file, import_source_folder
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.reporting.queries import (
    AmbiguousShipmentError,
    ReportingFilters,
    fetch_article_lines,
    fetch_shipment_detail,
    fetch_shipments,
    monthly_totals,
    period_totals,
)
from tests.fixtures import require_fixture_path
from tests.synthetic_sources import write_article_source, write_shipment_source


@pytest.fixture()
def imported_connection(tmp_path):
    connection = create_database(tmp_path / "cardmarket.db")
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    return connection


def test_fetch_article_lines_filters_by_date_direction_basis_and_order(imported_connection) -> None:
    sample = imported_connection.execute(
        """
        SELECT order_id, direction, date_basis, SUBSTR(event_datetime, 1, 10) AS event_date
        FROM article_lines
        ORDER BY article_line_id
        LIMIT 1
        """
    ).fetchone()
    rows = fetch_article_lines(
        imported_connection,
        ReportingFilters(
            start_date=sample["event_date"],
            end_date=sample["event_date"],
            direction=sample["direction"],
            date_basis=sample["date_basis"],
            order_id=sample["order_id"],
        ),
    )

    assert rows
    assert {row["order_id"] for row in rows} == {sample["order_id"]}
    assert {row["direction"] for row in rows} == {sample["direction"]}


def test_fetch_article_lines_filters_by_product_expansion_and_category(imported_connection) -> None:
    sample = imported_connection.execute(
        """
        SELECT product_id, article_name_snapshot, expansion_name_snapshot,
               category_name_snapshot
        FROM article_lines
        WHERE expansion_name_snapshot IS NOT NULL AND category_name_snapshot IS NOT NULL
        ORDER BY article_line_id
        LIMIT 1
        """
    ).fetchone()
    rows = fetch_article_lines(
        imported_connection,
        ReportingFilters(
            product_id=sample["product_id"],
            product_text=sample["article_name_snapshot"],
            expansion=sample["expansion_name_snapshot"],
            category=sample["category_name_snapshot"],
        ),
    )

    assert rows
    assert {row["product_id"] for row in rows} == {sample["product_id"]}


def test_fetch_shipments_filters_by_username_country_and_date(imported_connection) -> None:
    sample = imported_connection.execute(
        """
        SELECT shipments.order_id, shipments.direction, shipments.username, shipments.country,
               shipment_events.event_type,
               SUBSTR(shipment_events.event_datetime, 1, 10) AS event_date
        FROM shipments
        JOIN shipment_events USING (shipment_id)
        WHERE shipments.username IS NOT NULL AND shipments.country IS NOT NULL
        ORDER BY shipments.shipment_id
        LIMIT 1
        """
    ).fetchone()
    rows = fetch_shipments(
        imported_connection,
        ReportingFilters(
            start_date=sample["event_date"],
            end_date=sample["event_date"],
            direction=sample["direction"],
            date_basis=sample["event_type"],
            username=sample["username"],
            country=sample["country"],
        ),
    )

    assert len(rows) == 1
    assert rows[0]["order_id"] == sample["order_id"]


def test_period_totals_returns_counts_and_purchase_total(imported_connection) -> None:
    totals = period_totals(
        imported_connection,
        ReportingFilters(start_date="2016-06-01", end_date="2016-06-30"),
    )

    assert totals["article_line_count"] > 0
    assert totals["shipment_count"] > 0
    assert totals["purchase_total"] > 0
    assert totals["sales_total"] == 0


def test_monthly_totals_groups_by_month_and_direction(imported_connection) -> None:
    rows = monthly_totals(
        imported_connection,
        ReportingFilters(start_date="2016-06-01", end_date="2016-06-30"),
    )

    assert rows == [
        {
            "month": "2016-06",
            "direction": "PURCHASED",
            "article_line_count": rows[0]["article_line_count"],
            "shipment_count": rows[0]["shipment_count"],
            "total": rows[0]["total"],
        }
    ]


def test_shipment_detail_requires_direction_for_cross_direction_collision(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    source = tmp_path / "source"
    shared_order_id = "shared-order"
    for direction in ("PURCHASED", "SOLD"):
        path = write_shipment_source(
            source
            / f"{direction} SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV",
            order_id=shared_order_id,
        )
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))

    with pytest.raises(AmbiguousShipmentError):
        fetch_shipment_detail(connection, shared_order_id)

    purchased = fetch_shipment_detail(connection, shared_order_id, direction="PURCHASED")
    sold = fetch_shipment_detail(connection, shared_order_id, direction="SOLD")
    assert purchased is not None and purchased["direction"] == "PURCHASED"
    assert sold is not None and sold["direction"] == "SOLD"


def test_default_reporting_basis_does_not_double_count_event_views(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    source = tmp_path / "source"
    for basis in ("PURCHASEDATE", "PAYMENTDATE"):
        write_article_source(
            source / f"SOLD ARTICLES-BY{basis}-2026-08-01_2026-08-31.CSV"
        )
    import_source_folder(connection, source)

    default_totals = period_totals(connection)
    purchase_totals = period_totals(
        connection, ReportingFilters(date_basis="PURCHASEDATE")
    )
    all_views = period_totals(connection, ReportingFilters(date_basis=None))

    assert default_totals["article_line_count"] == 1
    assert default_totals["sales_total"] == 8
    assert purchase_totals["article_line_count"] == 1
    assert purchase_totals["sales_total"] == 8
    assert all_views["article_line_count"] == 2
    assert all_views["sales_total"] == 16


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
