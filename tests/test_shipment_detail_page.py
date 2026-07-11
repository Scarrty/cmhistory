from fastapi.testclient import TestClient

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.web.app import _mask_text, create_app
from tests.fixtures import require_fixture_path


def test_shipment_detail_page_shows_linked_articles_and_source_rows(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    sample = connection.execute(
        """
        SELECT shipments.order_id, shipments.username, article_lines.article_name_snapshot,
               import_files.file_name
        FROM shipments
        JOIN article_lines USING (shipment_id)
        JOIN import_files ON import_files.import_file_id = article_lines.source_import_file_id
        ORDER BY shipments.shipment_id, article_lines.article_line_id
        LIMIT 1
        """
    ).fetchone()
    client = TestClient(create_app(database_path=database_path))

    response = client.get(f"/shipments/{sample['order_id']}")

    assert response.status_code == 200
    assert f"Sendung {sample['order_id']}" in response.text
    assert "Zahlungsdatum" in response.text
    assert sample["article_name_snapshot"] in response.text
    assert sample["file_name"] in response.text
    assert _mask_text(sample["username"]) in response.text
    assert f">{sample['username']}<" not in response.text


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
