from urllib.parse import quote_plus

from fastapi.testclient import TestClient

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.reporting.queries import fetch_shipment_detail
from cm_dashboard.web.app import _mask_text, create_app
from tests.fixtures import require_fixture_path


def test_shipment_list_detail_and_article_pages_mask_private_fields(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    private_row = connection.execute(
        """
        SELECT shipments.*
        FROM shipments
        JOIN article_lines USING (shipment_id)
        WHERE username IS NOT NULL
        ORDER BY shipments.shipment_id
        LIMIT 1
        """
    ).fetchone()
    client = TestClient(create_app(database_path=database_path))

    for path in (
        f"/shipments?username={quote_plus(private_row['username'])}",
        f"/shipments/{private_row['order_id']}",
        f"/articles?username={quote_plus(private_row['username'])}",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert _mask_text(private_row["username"]) in response.text
        assert f">{private_row['username']}<" not in response.text
        for private_value in (
            private_row["counterparty_name"],
            private_row["street"],
            private_row["city"],
        ):
            if private_value:
                assert private_value not in response.text
        if path.startswith("/shipments/"):
            assert private_row["username"] not in response.text
        assert "VAT" not in response.text


def test_shipment_detail_query_excludes_sensitive_columns(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    path = require_fixture_path("unicode_shipment")
    import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    order_id = connection.execute(
        "SELECT order_id FROM shipments ORDER BY shipment_id LIMIT 1"
    ).fetchone()["order_id"]

    shipment = fetch_shipment_detail(connection, order_id)

    assert shipment is not None
    assert "counterparty_name" not in shipment
    assert "street" not in shipment
    assert "city" not in shipment
    assert "vat_id_present" not in shipment
    assert "is_professional" not in shipment


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
