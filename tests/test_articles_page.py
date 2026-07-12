from html import escape
from urllib.parse import urlencode

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.web.app import _mask_text
from tests.fixtures import require_fixture_path
from tests.webclient import make_client


def test_articles_page_filters_articles_and_links_to_shipments(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("tolerant_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    sample = connection.execute(
        """
        SELECT article_lines.*, shipments.username
        FROM article_lines
        JOIN shipments USING (shipment_id)
        WHERE expansion_name_snapshot IS NOT NULL AND category_name_snapshot IS NOT NULL
        ORDER BY article_line_id
        LIMIT 1
        """
    ).fetchone()
    client = make_client(database_path)

    query = urlencode(
        {
            "start_date": sample["event_datetime"][:10],
            "end_date": sample["event_datetime"][:10],
            "direction": sample["direction"],
            "date_basis": sample["date_basis"],
            "product_id": sample["product_id"],
            "product_text": sample["article_name_snapshot"],
            "expansion": sample["expansion_name_snapshot"],
            "category": sample["category_name_snapshot"],
        }
    )
    response = client.get(f"/articles?{query}")

    assert response.status_code == 200
    assert escape(sample["article_name_snapshot"]) in response.text
    assert (
        f'href="/shipments/{sample["order_id"]}?direction={sample["direction"]}'
        f'&amp;date_basis={sample["date_basis"]}"'
        in response.text
    )
    assert f'href="/products/{sample["product_id"]}"' in response.text
    assert escape(sample["category_name_snapshot"]) in response.text
    assert sample["date_basis"] in response.text
    assert _mask_text(sample["username"]) in response.text
    assert f">{sample['username']}<" not in response.text


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
