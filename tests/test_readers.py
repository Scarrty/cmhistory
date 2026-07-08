from cm_dashboard.importing.readers import read_spreadsheet
from tests.fixtures import require_fixture_path


def test_read_tolerant_xls_fixture_sheet_headers_rows_and_sample_cells() -> None:
    sheet = read_spreadsheet(require_fixture_path("tolerant_xls"))

    assert sheet.sheet_name == "Worksheet"
    assert sheet.headers
    assert "Shipment nr." in sheet.headers
    assert sheet.row_count > 0
    assert len(sheet.rows[0]) == len(sheet.headers)
    assert any(str(value).strip() for value in sheet.rows[0])


def test_read_csv_fixture_with_same_interface() -> None:
    sheet = read_spreadsheet(require_fixture_path("sold_articles_2026_01_csv"))

    assert sheet.sheet_name == "CSV"
    assert sheet.headers
    assert "Shipment nr." in sheet.headers
    assert sheet.row_count > 0
    assert all(len(row) == len(sheet.headers) for row in sheet.rows)


def test_unsupported_extension_is_explicit() -> None:
    try:
        read_spreadsheet("README.md")
    except ValueError as exc:
        assert "Unsupported spreadsheet extension" in str(exc)
    else:
        raise AssertionError("Expected unsupported extension to raise")
