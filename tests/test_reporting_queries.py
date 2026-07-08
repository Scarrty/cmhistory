import pytest

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.reporting.queries import (
    ReportingFilters,
    fetch_article_lines,
    fetch_shipments,
    monthly_totals,
    period_totals,
)
from tests.fixtures import require_fixture_path


@pytest.fixture()
def imported_connection(tmp_path):
    connection = create_database(tmp_path / "cardmarket.db")
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    return connection


def test_fetch_article_lines_filters_by_date_direction_basis_and_order(imported_connection) -> None:
    rows = fetch_article_lines(
        imported_connection,
        ReportingFilters(
            start_date="2016-06-01",
            end_date="2016-06-30",
            direction="PURCHASED",
            date_basis="PAYMENTDATE",
            order_id="38641681",
        ),
    )

    assert rows
    assert {row["order_id"] for row in rows} == {"38641681"}
    assert {row["direction"] for row in rows} == {"PURCHASED"}


def test_fetch_article_lines_filters_by_product_expansion_and_category(imported_connection) -> None:
    rows = fetch_article_lines(
        imported_connection,
        ReportingFilters(
            product_id="285547",
            product_text="Battle for Zendikar",
            expansion="Battle for Zendikar",
            category="Magic Lot",
        ),
    )

    assert len(rows) == 1
    assert rows[0]["product_id"] == "285547"


def test_fetch_shipments_filters_by_username_country_and_date(imported_connection) -> None:
    rows = fetch_shipments(
        imported_connection,
        ReportingFilters(
            start_date="2016-06-01",
            end_date="2016-06-30",
            direction="PURCHASED",
            date_basis="PAYMENTDATE",
            username="Shadwell",
            country="Germany",
        ),
    )

    assert len(rows) == 1
    assert rows[0]["order_id"] == "35389710"


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


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
