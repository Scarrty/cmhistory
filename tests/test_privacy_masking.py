from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.reporting.queries import fetch_shipment_detail
from cm_dashboard.web.app import create_app
from fastapi.testclient import TestClient
from tests.fixtures import require_fixture_path


def test_shipment_list_detail_and_article_pages_mask_private_fields(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    client = TestClient(create_app(database_path=database_path))

    for path in (
        "/shipments?username=Shadwell",
        "/shipments/35389710",
        "/articles?username=Shadwell",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert "S***l" in response.text
        assert ">Shadwell<" not in response.text
        assert "Claudius Hirsch" not in response.text
        assert "Haus F" not in response.text
        assert "59399 Olfen" not in response.text
        assert "VAT" not in response.text


def test_shipment_detail_query_excludes_sensitive_columns(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    path = require_fixture_path("unicode_shipment")
    import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))

    shipment = fetch_shipment_detail(connection, "35389710")

    assert shipment is not None
    assert "counterparty_name" not in shipment
    assert "street" not in shipment
    assert "city" not in shipment
    assert "vat_id_present" not in shipment
    assert "is_professional" not in shipment


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
