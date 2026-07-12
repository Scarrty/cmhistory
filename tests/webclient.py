"""TestClient factory that whitelists the TestClient host explicitly."""

from pathlib import Path

from fastapi.testclient import TestClient

from cm_dashboard.web.app import DEFAULT_ALLOWED_HOSTS, create_app


def make_client(database_path: str | Path) -> TestClient:
    return TestClient(
        create_app(
            database_path=database_path,
            allowed_hosts=[*DEFAULT_ALLOWED_HOSTS, "testserver"],
        )
    )
