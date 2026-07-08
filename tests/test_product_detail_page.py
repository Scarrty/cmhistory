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
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/products/273699")

    assert response.status_code == 200
    assert "Product 273699" in response.text
    assert "2 observed labels" in response.text
    assert "Charizard" in response.text
    assert "Glurak" in response.text
    assert "Article lines" in response.text
    assert "Purchases" in response.text
    assert "Sales" in response.text
    assert 'href="/shipments/7102735"' in response.text
    assert 'href="/shipments/22172074"' in response.text


def test_product_detail_page_returns_404_for_unknown_product(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    create_database(database_path)
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/products/unknown-product")

    assert response.status_code == 404


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
