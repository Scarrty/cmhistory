from urllib.parse import urlencode

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.web.app import _mask_text
from tests.fixtures import require_fixture_path
from tests.webclient import make_client


def test_shipments_page_filters_and_masks_username_by_default(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    path = require_fixture_path("unicode_shipment")
    import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    sample = connection.execute(
        """
        SELECT shipments.*, shipment_events.event_type,
               SUBSTR(shipment_events.event_datetime, 1, 10) AS event_date
        FROM shipments
        JOIN shipment_events USING (shipment_id)
        WHERE username IS NOT NULL AND country IS NOT NULL
        ORDER BY shipments.shipment_id
        LIMIT 1
        """
    ).fetchone()
    client = make_client(database_path)

    query = urlencode(
        {
            "start_date": sample["event_date"],
            "end_date": sample["event_date"],
            "direction": sample["direction"],
            "date_basis": sample["event_type"],
            "username": sample["username"],
            "country": sample["country"],
        }
    )
    response = client.get(f"/shipments?{query}")

    assert response.status_code == 200
    assert sample["order_id"] in response.text
    assert sample["country"] in response.text
    assert _mask_text(sample["username"]) in response.text
    assert f">{sample['username']}<" not in response.text


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
