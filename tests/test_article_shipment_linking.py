from cm_dashboard.db import create_database
from cm_dashboard.importing.article_import import (
    import_article_sheet,
    link_article_lines_to_shipments,
)
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.pipeline import import_source_folder
from cm_dashboard.importing.raw_store import upsert_import_file
from cm_dashboard.importing.readers import WorksheetData, read_spreadsheet
from cm_dashboard.importing.shipment_import import import_shipment_sheet
from tests.fixtures import require_fixture_path
from tests.synthetic_sources import write_article_source, write_shipment_source


def test_articles_imported_before_shipments_are_linked_after_shipment_import(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    article_path = require_fixture_path("tolerant_xls")
    shipment_path = require_fixture_path("unicode_shipment")
    article_metadata = require_parsed_filename(article_path)
    shipment_metadata = require_parsed_filename(shipment_path)
    article_sheet = read_spreadsheet(article_path)
    shipment_sheet = read_spreadsheet(shipment_path)
    article_import_file_id = upsert_import_file(
        connection,
        path=article_path,
        metadata=article_metadata,
        sheet_name=article_sheet.sheet_name,
        row_count=article_sheet.row_count,
    )
    shipment_import_file_id = upsert_import_file(
        connection,
        path=shipment_path,
        metadata=shipment_metadata,
        sheet_name=shipment_sheet.sheet_name,
        row_count=shipment_sheet.row_count,
    )

    import_article_sheet(
        connection,
        import_file_id=article_import_file_id,
        sheet=article_sheet,
        metadata=article_metadata,
    )
    assert connection.execute(
        "SELECT COUNT(*) FROM article_lines WHERE shipment_id IS NULL"
    ).fetchone()[0] == article_sheet.row_count

    import_shipment_sheet(
        connection,
        import_file_id=shipment_import_file_id,
        sheet=shipment_sheet,
        metadata=shipment_metadata,
    )

    assert connection.execute(
        "SELECT COUNT(*) FROM article_lines WHERE shipment_id IS NULL"
    ).fetchone()[0] == 0


def test_unmatched_article_orders_are_reported_as_import_issues(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )
    sheet = WorksheetData(
        path="in-memory.csv",
        sheet_name="CSV",
        headers=(
            "Shipment nr.",
            "Date of purchase",
            "Article",
            "Product ID",
            "Localized Product Name",
            "Expansion",
            "Category",
            "Amount",
            "Article Value",
            "Total",
            "Currency",
            "Comments",
        ),
        rows=(
            (
                "missing-order",
                "2026-01-01 10:00:00",
                "Card",
                "123",
                "Card",
                "Set",
                "Category",
                "1",
                "1.00",
                "1.00",
                "EUR",
                "",
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
    import_article_sheet(
        connection,
        import_file_id=import_file_id,
        sheet=sheet,
        metadata=metadata,
    )

    result = link_article_lines_to_shipments(connection)

    assert result.linked_count == 0
    assert result.unmatched_order_ids == ("missing-order",)
    issue = connection.execute("SELECT * FROM import_issues").fetchone()
    assert issue["code"] == "unmatched_article_order"
    assert "missing-order" in issue["message"]


def test_same_order_id_in_both_directions_links_to_separate_shipments(tmp_path) -> None:
    source = tmp_path / "source"
    shared_order_id = "shared-order"
    write_article_source(
        source / "PURCHASED ARTICLES-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV",
        overrides={"Shipment nr.": shared_order_id},
    )
    write_shipment_source(
        source / "PURCHASED SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV",
        order_id=shared_order_id,
    )
    write_article_source(
        source / "SOLD ARTICLES-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV",
        overrides={"Shipment nr.": shared_order_id},
    )
    write_shipment_source(
        source / "SOLD SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV",
        order_id=shared_order_id,
    )
    connection = create_database(tmp_path / "cardmarket.db")

    results = import_source_folder(connection, source)

    assert {result.status for result in results} == {"imported"}
    assert connection.execute(
        "SELECT COUNT(*) FROM shipments WHERE order_id = ?", (shared_order_id,)
    ).fetchone()[0] == 2
    links = connection.execute(
        """
        SELECT article_lines.direction AS article_direction,
               shipments.direction AS shipment_direction
        FROM article_lines
        JOIN shipments USING (shipment_id)
        WHERE article_lines.order_id = ?
        ORDER BY article_lines.direction
        """,
        (shared_order_id,),
    ).fetchall()
    assert [(row["article_direction"], row["shipment_direction"]) for row in links] == [
        ("PURCHASED", "PURCHASED"),
        ("SOLD", "SOLD"),
    ]
