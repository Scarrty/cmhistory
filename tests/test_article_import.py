from cm_dashboard.db import create_database
from cm_dashboard.importing.article_import import import_article_sheet
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.normalize import (
    normalize_currency,
    normalize_decimal,
    normalize_identifier,
    normalize_int,
)
from cm_dashboard.importing.raw_store import upsert_import_file
from cm_dashboard.importing.readers import WorksheetData, read_spreadsheet
from tests.fixtures import require_fixture_path


def test_import_article_sheet_normalizes_products_labels_and_lines(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    path = require_fixture_path("tolerant_xls")
    metadata = require_parsed_filename(path)
    sheet = read_spreadsheet(path)
    import_file_id = upsert_import_file(
        connection,
        path=path,
        metadata=metadata,
        sheet_name=sheet.sheet_name,
        row_count=sheet.row_count,
    )

    imported_count = import_article_sheet(
        connection,
        import_file_id=import_file_id,
        sheet=sheet,
        metadata=metadata,
    )

    assert imported_count == sheet.row_count
    assert connection.execute("SELECT COUNT(*) FROM article_lines").fetchone()[0] == sheet.row_count
    assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0
    row = connection.execute(
        "SELECT * FROM article_lines ORDER BY article_line_id LIMIT 1"
    ).fetchone()
    private_source_row = dict(zip(sheet.headers, sheet.rows[0], strict=True))
    assert row["order_id"] == normalize_identifier(private_source_row["Shipment nr."])
    assert row["product_id"] == normalize_identifier(private_source_row["Product ID"])
    assert row["quantity"] == normalize_int(private_source_row["Amount"])
    assert row["article_value"] == str(normalize_decimal(private_source_row["Article Value"]))
    assert row["currency"] == normalize_currency(private_source_row["Currency"])


def test_import_article_sheet_keeps_multiple_observed_labels_for_one_product(tmp_path) -> None:
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
                "1",
                "2026-01-01 10:00:00",
                "Charizard",
                "123",
                "Charizard",
                "Base Set",
                "Pokemon Single",
                "1",
                "10.00",
                "10.00",
                "EUR",
                "",
            ),
            (
                "2",
                "2026-01-02 10:00:00",
                "Glurak",
                "123",
                "Glurak",
                "Base Set",
                "Pokemon Single",
                "1",
                "11.00",
                "11.00",
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

    labels = {
        row["label"]
        for row in connection.execute(
            "SELECT label FROM product_labels WHERE product_id = '123'"
        ).fetchall()
    }
    assert labels == {"Charizard", "Glurak"}


def test_import_article_sheet_preserves_repeated_identical_positions(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )
    row = (
        "same-order",
        "2026-01-01 10:00:00",
        "Synthetic Card",
        "123",
        "Synthetic Card",
        "Synthetic Set",
        "Synthetic Category",
        "1",
        "8.0",
        "8.0",
        "EUR",
        "",
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
        rows=(row, row),
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

    assert connection.execute("SELECT COUNT(*) FROM article_lines").fetchone()[0] == 2
