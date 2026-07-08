from fastapi.testclient import TestClient

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.web.app import create_app
from tests.fixtures import require_fixture_path


def test_shipments_page_filters_and_masks_username_by_default(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    path = require_fixture_path("unicode_shipment")
    import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    client = TestClient(create_app(database_path=database_path))

    response = client.get(
        "/shipments?start_date=2016-06-01&end_date=2016-06-30"
        "&direction=PURCHASED&date_basis=PAYMENTDATE&username=Shadwell&country=Germany"
    )

    assert response.status_code == 200
    assert "35389710" in response.text
    assert "Germany" in response.text
    assert "S***l" in response.text
    assert ">Shadwell<" not in response.text


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
