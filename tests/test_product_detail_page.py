from fastapi.testclient import TestClient

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.web.app import create_app
from tests.fixtures import require_fixture_path


def test_product_detail_page_shows_labels_totals_and_article_lines(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    for key in ("charizard_2016_payment_articles", "charizard_2020_payment_articles"):
        path = require_fixture_path(key)
        import_source_file(connection, SourceFile(path=path, metadata=_metadata(path)))
    product = connection.execute(
        """
        SELECT product_id, COUNT(*) AS label_count
        FROM product_labels
        GROUP BY product_id
        HAVING COUNT(*) > 1
        ORDER BY product_id
        LIMIT 1
        """
    ).fetchone()
    labels = [
        row["label"]
        for row in connection.execute(
            "SELECT label FROM product_labels WHERE product_id = ? ORDER BY label",
            (product["product_id"],),
        ).fetchall()
    ]
    orders = [
        (row["order_id"], row["direction"])
        for row in connection.execute(
            """
            SELECT DISTINCT order_id, direction
            FROM article_lines
            WHERE product_id = ?
            ORDER BY direction, order_id
            """,
            (product["product_id"],),
        ).fetchall()
    ]
    client = TestClient(create_app(database_path=database_path))

    response = client.get(f"/products/{product['product_id']}")

    assert response.status_code == 200
    assert f"Product {product['product_id']}" in response.text
    assert f"{product['label_count']} observed labels" in response.text
    for label in labels:
        assert label in response.text
    assert "Article lines" in response.text
    assert "Purchases" in response.text
    assert "Sales" in response.text
    for order_id, direction in orders:
        assert f'href="/shipments/{order_id}?direction={direction}"' in response.text


def test_product_detail_page_returns_404_for_unknown_product(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    create_database(database_path)
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/products/unknown-product")

    assert response.status_code == 404


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
