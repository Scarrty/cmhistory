from fastapi.testclient import TestClient

from cm_dashboard.db import create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.raw_store import upsert_import_file
from cm_dashboard.web.app import create_app
from tests.fixtures import require_fixture_path


def test_import_status_page_shows_import_files_and_issues(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    source_path = require_fixture_path("tolerant_xls")
    metadata = require_parsed_filename(source_path)
    import_file_id = upsert_import_file(
        connection,
        path=source_path,
        metadata=metadata,
        sheet_name="Worksheet",
        row_count=42,
        import_status="imported",
    )
    connection.execute(
        """
        INSERT INTO import_issues (
            import_file_id, severity, code, message, source_row_number
        ) VALUES (?, 'warning', 'example_warning', 'Example warning', 7)
        """,
        (import_file_id,),
    )
    connection.commit()
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/imports")

    assert response.status_code == 200
    assert source_path.name in response.text
    assert "PAYMENTDATE" in response.text
    assert "42" in response.text
    assert "example_warning" in response.text
    assert "Example warning" in response.text
