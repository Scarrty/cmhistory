from fastapi.testclient import TestClient

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.web.app import create_app
from tests.fixtures import require_fixture_path


def test_articles_page_filters_articles_and_links_to_shipments(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    client = TestClient(create_app(database_path=database_path))

    response = client.get(
        "/articles?start_date=2016-06-01&end_date=2016-06-30"
        "&direction=PURCHASED&date_basis=PAYMENTDATE"
        "&product_id=285547&product_text=Battle+for+Zendikar"
        "&expansion=Battle+for+Zendikar&category=Magic+Lot"
    )

    assert response.status_code == 200
    assert "Battle for Zendikar: Land Pack" in response.text
    assert 'href="/shipments/38641681"' in response.text
    assert 'href="/products/285547"' in response.text
    assert "Magic Lot" in response.text
    assert "PAYMENTDATE" in response.text
    assert "S***s" in response.text
    assert ">Schlabbes<" not in response.text
    assert "Obelisk of Urd" not in response.text


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
