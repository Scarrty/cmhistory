

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from tests.fixtures import require_fixture_path
from tests.webclient import make_client


def test_dashboard_page_renders_filtered_kpis_and_monthly_chart(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    client = make_client(database_path)

    response = client.get("/?start_date=2016-06-01&end_date=2016-06-30")

    assert response.status_code == 200
    assert "Artikelpositionen" in response.text
    assert "Sendungen" in response.text
    assert "2016-06" in response.text
    assert "data-chart-bar" in response.text
    assert "Gekauft" in response.text
    assert '<option value="PAYMENTDATE" selected>Zahlungsdatum</option>' in response.text


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
