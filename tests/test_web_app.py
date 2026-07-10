from fastapi.testclient import TestClient

from cm_dashboard.web.app import create_app


def test_web_app_starts_and_serves_base_route() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Cardmarket History" in response.text
    assert "Dashboard" in response.text


def test_web_app_serves_static_css() -> None:
    client = TestClient(create_app())

    response = client.get("/static/app.css")

    assert response.status_code == 200
    assert "font-family" in response.text


def test_web_app_rejects_invalid_filter_values() -> None:
    client = TestClient(create_app(database_path=":memory:"))

    assert client.get("/?direction=invalid").status_code == 422
    assert client.get("/?date_basis=invalid").status_code == 422
    assert client.get("/?start_date=not-a-date").status_code == 422
    assert client.get("/?start_date=2026-08-02&end_date=2026-08-01").status_code == 422
