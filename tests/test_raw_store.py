import json

from cm_dashboard.db import create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.normalize import normalize_identifier
from cm_dashboard.importing.raw_store import (
    file_sha256,
    store_raw_article_rows,
    store_raw_shipment_rows,
    upsert_import_file,
)
from cm_dashboard.importing.readers import read_spreadsheet
from cm_dashboard.importing.shipment_grouping import resolve_shipment_groups
from tests.fixtures import require_fixture_path


def test_upsert_import_file_stores_metadata_and_hash(tmp_path) -> None:
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

    row = connection.execute(
        "SELECT * FROM import_files WHERE import_file_id = ?",
        (import_file_id,),
    ).fetchone()
    assert row["file_name"] == path.name
    assert row["file_hash"] == file_sha256(path)
    assert row["sheet_name"] == "Worksheet"
    assert row["row_count"] == sheet.row_count
    assert row["direction"] == "PURCHASED"


def test_store_raw_article_rows_persists_source_traceability(tmp_path) -> None:
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

    stored_count = store_raw_article_rows(
        connection,
        import_file_id=import_file_id,
        sheet=sheet,
        metadata=metadata,
    )

    assert stored_count == sheet.row_count
    row = connection.execute(
        """
        SELECT * FROM raw_article_rows
        WHERE import_file_id = ?
        ORDER BY source_row_number
        LIMIT 1
        """,
        (import_file_id,),
    ).fetchone()
    raw_values = json.loads(row["raw_values_json"])
    private_source_row = dict(zip(sheet.headers, sheet.rows[0], strict=True))
    assert row["source_row_number"] == 2
    assert row["order_id"] == normalize_identifier(private_source_row["Shipment nr."])
    assert raw_values["Shipment nr."] == private_source_row["Shipment nr."]
    assert row["business_key"]


def test_store_raw_shipment_rows_persists_resolved_order_ids(tmp_path) -> None:
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

    stored_count = store_raw_shipment_rows(connection, import_file_id=import_file_id, sheet=sheet)

    assert stored_count == sheet.row_count
    private_continuation = next(
        row
        for row in resolve_shipment_groups(sheet)
        if not row.is_header_row and row.resolved_order_id is not None
    )
    row = connection.execute(
        """
        SELECT * FROM raw_shipment_rows
        WHERE import_file_id = ? AND source_row_number = ?
        """,
        (import_file_id, private_continuation.source_row_number),
    ).fetchone()
    inherited_values = json.loads(row["inherited_values_json"])
    raw_values = json.loads(row["raw_values_json"])
    assert row["order_id"] is None
    assert row["resolved_order_id"] == private_continuation.resolved_order_id
    assert row["is_header_row"] == 0
    assert raw_values["OrderID"] == ""
    assert inherited_values["Username"] == private_continuation.inherited_values["Username"]
