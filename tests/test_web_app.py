import importlib
import sys

from fastapi.testclient import TestClient

import cm_dashboard.web.app as web_app
from cm_dashboard.db import connect_database, create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.raw_store import upsert_import_file
from cm_dashboard.web.app import create_app


def test_importing_web_app_module_creates_no_database(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    sys.modules.pop("cm_dashboard.web.app", None)
    try:
        importlib.import_module("cm_dashboard.web.app")

        assert not (tmp_path / "data").exists()
    finally:
        sys.modules.pop("cm_dashboard.web.app", None)
        importlib.import_module("cm_dashboard.web.app")


def test_web_app_starts_and_serves_base_route(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    response = client.get("/")

    assert response.status_code == 200
    assert "Cardmarket History" in response.text
    assert "Dashboard" in response.text
    assert '<html lang="de">' in response.text
    assert '<a class="skip-link" href="#main-content">Zum Inhalt</a>' in response.text
    assert 'id="main-content" tabindex="-1"' in response.text


def test_web_app_serves_static_css(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    response = client.get("/static/app.css")

    assert response.status_code == 200
    assert "font-family" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_web_app_rejects_invalid_filter_values(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    assert client.get("/?direction=invalid").status_code == 422
    assert client.get("/?date_basis=invalid").status_code == 422
    assert client.get("/?start_date=not-a-date").status_code == 422
    assert client.get("/?start_date=2026-08-02&end_date=2026-08-01").status_code == 422
    assert client.get("/articles?page=0").status_code == 422
    assert client.get("/shipments?page=not-a-number").status_code == 422
    assert client.get("/imports?file_page=0").status_code == 422
    assert client.get("/imports?issue_page=not-a-number").status_code == 422
    assert client.get("/articles?min_amount=NaN").status_code == 422
    assert client.get("/articles?min_amount=10&max_amount=9").status_code == 422
    assert client.get("/articles?min_quantity=1.5").status_code == 422
    assert client.get("/articles?min_quantity=2&max_quantity=1").status_code == 422
    assert client.get("/articles?import_status=unknown").status_code == 422
    assert client.get("/articles?link_status=unknown").status_code == 422


def test_article_page_retains_advanced_filter_values(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    response = client.get(
        "/articles?currency=eur&min_amount=1.25&max_quantity=4"
        "&comments=note&import_status=imported&link_status=linked"
    )

    assert response.status_code == 200
    assert 'name="currency" value="EUR"' in response.text
    assert 'name="min_amount" type="number" step="0.01" value="1.25"' in response.text
    assert 'name="max_quantity" type="number" min="0" step="1" value="4"' in response.text
    assert '<option value="imported" selected>Importiert</option>' in response.text
    assert '<option value="linked" selected>Verkn&uuml;pft</option>' in response.text


def test_article_pages_expose_all_filtered_rows(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    connection.executemany(
        """
        INSERT INTO article_lines(
            order_id, direction, date_basis, event_datetime,
            article_name_snapshot, quantity, article_value, total, currency, business_key
        )
        VALUES (?, 'SOLD', 'PAYMENTDATE', '2026-08-12 10:00:00',
                'Synthetic Card', 1, '8', '8', 'EUR', ?)
        """,
        [(f"order-{index:04d}", f"article-key-{index}") for index in range(105)],
    )
    connection.commit()
    connection.close()
    client = TestClient(create_app(database_path=database_path))

    first_page = client.get("/articles?direction=SOLD")
    second_page = client.get("/articles?direction=SOLD&page=2")

    assert first_page.status_code == 200
    assert "1&ndash;100 von 105" in first_page.text
    assert 'href="/articles?direction=SOLD&amp;page=2"' in first_page.text
    assert second_page.status_code == 200
    assert "101&ndash;105 von 105" in second_page.text
    assert "Seite 2 von 2" in second_page.text
    assert "order-0000" in second_page.text


def test_web_app_sets_local_security_headers_and_rejects_unknown_hosts(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    response = client.get("/")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/", headers={"host": "untrusted.example"}).status_code == 400


def test_web_app_closes_request_database_connections(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "cardmarket.db"
    create_database(database_path).close()
    opened = []

    class ConnectionProxy:
        def __init__(self, connection):
            self.connection = connection
            self.closed = False

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def close(self):
            self.closed = True
            self.connection.close()

    def tracked_connect(path):
        proxy = ConnectionProxy(connect_database(path))
        opened.append(proxy)
        return proxy

    monkeypatch.setattr(web_app, "connect_database", tracked_connect)
    client = TestClient(create_app(database_path=database_path))

    assert client.get("/").status_code == 200
    assert len(opened) == 1
    assert opened[0].closed


def test_web_app_refuses_to_report_from_outdated_normalization(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV"
    )
    upsert_import_file(
        connection,
        path=__file__,
        metadata=metadata,
        import_status="imported",
        normalization_version=1,
    )
    connection.commit()
    connection.close()
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/")

    assert response.status_code == 503
    assert "rebuild" in response.json()["detail"]
