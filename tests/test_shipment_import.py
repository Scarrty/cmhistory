from cm_dashboard.db import create_database
from cm_dashboard.importing.filename import require_parsed_filename
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
    assert connection.execute("SELECT COUNT(*) FROM shipments").fetchone()[0] == expected_header_count
    shipment = connection.execute(
        "SELECT * FROM shipments WHERE order_id = '35389710'"
    ).fetchone()
    assert shipment["username"] == "Shadwell"
    assert shipment["country"] == "Germany"
    assert shipment["is_professional"] == 1
    assert shipment["vat_id_present"] == 1
    assert shipment["article_count"] == 24
    assert shipment["trustee_service_fee"] == "0.00"
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
        path="in-memory.xls",
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
