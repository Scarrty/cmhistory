from pathlib import Path

from cm_dashboard.db import create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.normalize import (
    normalize_bool,
    normalize_identifier,
    normalize_int,
    normalize_text,
)
from cm_dashboard.importing.raw_store import upsert_import_file
from cm_dashboard.importing.readers import WorksheetData, read_spreadsheet
from cm_dashboard.importing.shipment_grouping import resolve_shipment_groups
from cm_dashboard.importing.shipment_import import import_shipment_sheet
from tests.fixtures import require_fixture_path


def test_import_shipment_sheet_normalizes_shipments_events_and_fees(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    path = require_fixture_path("unicode_shipment")
    metadata = require_parsed_filename(path)
    sheet = read_spreadsheet(path)
    import_file_id = upsert_import_file(
        connection,
        path=path,
        metadata=metadata,
        sheet_name=sheet.sheet_name,
        row_count=sheet.row_count,
    )
    expected_header_count = sum(row.is_header_row for row in resolve_shipment_groups(sheet))

    imported_count = import_shipment_sheet(
        connection,
        import_file_id=import_file_id,
        sheet=sheet,
        metadata=metadata,
    )

    assert imported_count == expected_header_count
    shipment_count = connection.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
    assert shipment_count == expected_header_count
    private_header = next(row for row in resolve_shipment_groups(sheet) if row.is_header_row)
    private_order_id = normalize_identifier(private_header.values["OrderID"])
    shipment = connection.execute(
        "SELECT * FROM shipments WHERE order_id = ?", (private_order_id,)
    ).fetchone()
    assert shipment["username"] == normalize_text(private_header.values["Username"])
    assert shipment["country"] == normalize_text(private_header.values["Country"])
    expected_is_professional = normalize_bool(private_header.values["Is Professional"])
    assert shipment["is_professional"] == (
        None if expected_is_professional is None else int(expected_is_professional)
    )
    assert shipment["vat_id_present"] == int(
        normalize_text(private_header.values["VAT Number"]) is not None
    )
    assert shipment["article_count"] == normalize_int(private_header.values["Article Count"])
    assert shipment["trustee_service_fee"] is not None
    assert shipment["commission"] is None
    event = connection.execute(
        """
        SELECT * FROM shipment_events
        WHERE shipment_id = ? AND event_type = 'PAYMENTDATE'
        """,
        (shipment["shipment_id"],),
    ).fetchone()
    assert event["event_datetime"].startswith("2016-06-")


def test_import_shipment_sheet_uses_commission_for_sold_shipments(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    metadata = require_parsed_filename(
        "SOLD SHIPMENTS-BYPAYMENTDATE-2026-01-01_2026-01-31.XLS"
    )
    sheet = WorksheetData(
        path=Path("in-memory.xls"),
        sheet_name="Worksheet",
        headers=(
            "OrderID",
            "Username",
            "Name",
            "Street",
            "City",
            "Country",
            "Is Professional",
            "VAT Number",
            "Date of Payment",
            "Article Count",
            "Merchandise Value",
            "Shipment Costs",
            "Total Value",
            "Commission",
            "Currency",
            "Description",
            "Product ID",
            "Localized Product Name",
        ),
        rows=(
            (
                "1",
                "buyer",
                "Name",
                "Street",
                "City",
                "Germany",
                "",
                "",
                "2026-01-01 10:00:00",
                "1",
                "10,00",
                "1,50",
                "11,50",
                "0,50",
                "EUR",
                "1x Card",
                "123",
                "Card",
            ),
        ),
    )
    import_file_id = upsert_import_file(
        connection,
        path=__file__,
        metadata=metadata,
        sheet_name=sheet.sheet_name,
        row_count=sheet.row_count,
    )

    import_shipment_sheet(
        connection,
        import_file_id=import_file_id,
        sheet=sheet,
        metadata=metadata,
    )

    shipment = connection.execute("SELECT * FROM shipments WHERE order_id = '1'").fetchone()
    assert shipment["commission"] == "0.50"
    assert shipment["trustee_service_fee"] is None


def test_import_shipment_sheet_reports_orphan_continuation_rows(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    metadata = require_parsed_filename(
        "SOLD SHIPMENTS-BYPAYMENTDATE-2026-01-01_2026-01-31.XLS"
    )
    sheet = WorksheetData(
        path=Path("in-memory.xls"),
        sheet_name="Worksheet",
        headers=("OrderID", "Username", "Date of Payment", "Description"),
        rows=(
            ("", "", "", "1x Orphan Card"),
            ("1", "buyer", "2026-01-01 10:00:00", "1x Card"),
        ),
    )
    import_file_id = upsert_import_file(
        connection,
        path=__file__,
        metadata=metadata,
        sheet_name=sheet.sheet_name,
        row_count=sheet.row_count,
    )

    imported_count = import_shipment_sheet(
        connection,
        import_file_id=import_file_id,
        sheet=sheet,
        metadata=metadata,
    )

    assert imported_count == 1
    issue = connection.execute(
        "SELECT * FROM import_issues WHERE code = 'orphan_shipment_row'"
    ).fetchone()
    assert issue is not None
    assert issue["source_row_number"] == 2
    assert "no preceding" in issue["message"]


def test_import_shipment_sheet_reports_missing_event_dates_without_crashing(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    metadata = require_parsed_filename(
        "PURCHASED SHIPMENTS-BYPAYMENTDATE-2026-01-01_2026-01-31.XLS"
    )
    sheet = WorksheetData(
        path=Path("in-memory.xls"),
        sheet_name="Worksheet",
        headers=(
            "OrderID",
            "Username",
            "Name",
            "Street",
            "City",
            "Country",
            "Is Professional",
            "VAT Number",
            "Date of Payment",
            "Article Count",
            "Merchandise Value",
            "Shipment Costs",
            "Trustee service fee",
            "Total Value",
            "Currency",
            "Description",
            "Product ID",
            "Localized Product Name",
        ),
        rows=(
            (
                "missing-date",
                "seller",
                "Name",
                "Street",
                "City",
                "Germany",
                "",
                "",
                "",
                "1",
                "10,00",
                "1,50",
                "0,00",
                "11,50",
                "EUR",
                "1x Card",
                "123",
                "Card",
            ),
        ),
    )
    import_file_id = upsert_import_file(
        connection,
        path=__file__,
        metadata=metadata,
        sheet_name=sheet.sheet_name,
        row_count=sheet.row_count,
    )

    imported_count = import_shipment_sheet(
        connection,
        import_file_id=import_file_id,
        sheet=sheet,
        metadata=metadata,
    )

    assert imported_count == 1
    assert connection.execute("SELECT COUNT(*) FROM shipments").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM shipment_events").fetchone()[0] == 0
    issue = connection.execute("SELECT * FROM import_issues").fetchone()
    assert issue["code"] == "missing_shipment_event_date"
    assert issue["source_row_number"] == 2
