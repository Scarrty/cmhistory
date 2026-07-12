from zipfile import ZIP_DEFLATED, ZipFile

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


def test_read_xlsx_with_same_interface(tmp_path) -> None:
    path = tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.XLSX"
    _write_minimal_xlsx(path)

    sheet = read_spreadsheet(path)

    assert sheet.sheet_name == "Worksheet"
    assert sheet.headers == ("Shipment nr.", "Article")
    assert sheet.rows == ((1001.0, "Synthetic Card"),)


def test_read_xls_preserves_unicode_text() -> None:
    sheet = read_spreadsheet(require_fixture_path("unicode_shipment"))
    street_index = sheet.headers.index("Street")
    private_street_values = [str(row[street_index]) for row in sheet.rows if row[street_index]]

    assert any(any(ord(character) > 127 for character in value) for value in private_street_values)
    assert all("\ufffd" not in value for value in private_street_values)


def test_read_csv_preserves_newlines_inside_quoted_fields(tmp_path) -> None:
    path = tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.CSV"
    path.write_text(
        'Shipment nr.;Comments\n1001;"line1\nline2"\n1002;plain\n',
        encoding="utf-8",
    )

    sheet = read_spreadsheet(path)

    assert sheet.row_count == 2
    assert sheet.rows[0] == ("1001", "line1\nline2")
    assert sheet.rows[1] == ("1002", "plain")


def test_read_csv_rejects_rows_with_extra_non_empty_cells(tmp_path) -> None:
    path = tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.CSV"
    path.write_text(
        "Shipment nr.;Comments\n1001;ok\n1002;broken;overflow\n",
        encoding="utf-8",
    )

    try:
        read_spreadsheet(path)
    except ValueError as exc:
        assert "Row 3" in str(exc)
    else:
        raise AssertionError("Expected overlong row to raise")


def test_read_csv_tolerates_trailing_empty_cells(tmp_path) -> None:
    path = tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.CSV"
    path.write_text(
        "Shipment nr.;Comments\n1001;ok;\n",
        encoding="utf-8",
    )

    sheet = read_spreadsheet(path)

    assert sheet.rows == (("1001", "ok"),)


def test_unsupported_extension_is_explicit() -> None:
    try:
        read_spreadsheet("README.md")
    except ValueError as exc:
        assert "Unsupported spreadsheet extension" in str(exc)
    else:
        raise AssertionError("Expected unsupported extension to raise")


def _write_minimal_xlsx(path) -> None:
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="xl/workbook.xml"/>
</Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Worksheet" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
</Relationships>""",
        "xl/worksheets/sheet1.xml": """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>Shipment nr.</t></is></c>
      <c r="B1" t="inlineStr"><is><t>Article</t></is></c>
    </row>
    <row r="2">
      <c r="A2"><v>1001</v></c>
      <c r="B2" t="inlineStr"><is><t>Synthetic Card</t></is></c>
    </row>
  </sheetData>
</worksheet>""",
    }
    with ZipFile(path, "w", ZIP_DEFLATED) as workbook:
        for name, content in files.items():
            workbook.writestr(name, content)
