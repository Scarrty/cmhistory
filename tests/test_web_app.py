from fastapi.testclient import TestClient

import cm_dashboard.web.app as web_app
from cm_dashboard.db import connect_database, create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.raw_store import upsert_import_file
from cm_dashboard.web.app import create_app


def test_web_app_starts_and_serves_base_route(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    response = client.get("/")

    assert response.status_code == 200
    assert "Cardmarket History" in response.text
    assert "Dashboard" in response.text


def test_web_app_serves_static_css(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    response = client.get("/static/app.css")

    assert response.status_code == 200
    assert "font-family" in response.text


def test_web_app_rejects_invalid_filter_values(tmp_path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "cardmarket.db"))

    assert client.get("/?direction=invalid").status_code == 422
    assert client.get("/?date_basis=invalid").status_code == 422
    assert client.get("/?start_date=not-a-date").status_code == 422
    assert client.get("/?start_date=2026-08-02&end_date=2026-08-01").status_code == 422


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
