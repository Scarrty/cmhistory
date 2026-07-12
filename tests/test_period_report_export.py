import csv
from io import StringIO

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from tests.fixtures import require_fixture_path
from tests.webclient import make_client


def test_period_report_csv_uses_filters_and_expected_headers(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    path = require_fixture_path("tolerant_xls")
    import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    client = make_client(database_path)

    response = client.get(
        "/reports/period.csv?start_date=2016-06-01&end_date=2016-06-30"
        "&direction=PURCHASED&date_basis=PAYMENTDATE&product_id=285547"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="period-report.csv"'
    rows = list(csv.DictReader(StringIO(response.text)))
    assert rows[0].keys() == {
        "section",
        "date_basis",
        "month",
        "direction",
        "article_line_count",
        "shipment_count",
        "purchase_total",
        "sales_total",
        "total",
        "net_total",
    }
    assert rows[0] == {
        "section": "period",
        "date_basis": "PAYMENTDATE",
        "month": "",
        "direction": "ALL",
        "article_line_count": "1",
        "shipment_count": "1",
        "purchase_total": "39.6",
        "sales_total": "0",
        "total": "39.6",
        "net_total": "-39.6",
    }
    assert rows[1]["section"] == "monthly"
    assert rows[1]["date_basis"] == "PAYMENTDATE"
    assert rows[1]["month"] == "2016-06"
    assert rows[1]["direction"] == "PURCHASED"
    assert rows[1]["total"] == "39.6"
    assert rows[1]["net_total"] == "-39.6"


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
