from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.web.app import create_app
from fastapi.testclient import TestClient
from tests.fixtures import require_fixture_path


def test_dashboard_page_renders_filtered_kpis_and_monthly_chart(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/?start_date=2016-06-01&end_date=2016-06-30")

    assert response.status_code == 200
    assert "Article lines" in response.text
    assert "Shipments" in response.text
    assert "2016-06" in response.text
    assert "data-chart-bar" in response.text
    assert "PURCHASED" in response.text


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
