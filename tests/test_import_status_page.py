

from cm_dashboard.db import create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.raw_store import upsert_import_file
from cm_dashboard.importing.version import NORMALIZATION_VERSION
from tests.fixtures import require_fixture_path
from tests.webclient import make_client


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
    client = make_client(database_path)

    response = client.get("/imports")

    assert response.status_code == 200
    assert source_path.name in response.text
    assert "Zahlungsdatum" in response.text
    assert "42" in response.text
    assert "example_warning" in response.text
    assert "Example warning" in response.text


def test_import_status_page_paginates_files_and_issues_independently(tmp_path) -> None:
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    connection.executemany(
        """
        INSERT INTO import_files(
            original_path, file_name, file_extension, direction, entity, date_basis,
            period_start, period_end, import_status, normalization_version
        )
        VALUES (?, ?, '.CSV', 'SOLD', 'ARTICLES', 'PAYMENTDATE',
                '2026-08-01', '2026-08-31', 'imported', ?)
        """,
        [
            (f"source-{index}", f"file-{index:03d}.CSV", NORMALIZATION_VERSION)
            for index in range(105)
        ],
    )
    connection.executemany(
        """
        INSERT INTO import_issues(severity, code, message)
        VALUES ('warning', ?, ?)
        """,
        [(f"issue-{index:03d}", f"Issue {index:03d}") for index in range(105)],
    )
    connection.commit()
    connection.close()
    client = make_client(database_path)

    first_page = client.get("/imports")
    second_page = client.get("/imports?file_page=2&issue_page=2")

    assert first_page.status_code == 200
    assert "105 Dateien" in first_page.text
    assert "105 Eintr&auml;ge" in first_page.text
    assert 'href="/imports?file_page=2"' in first_page.text
    assert 'href="/imports?issue_page=2"' in first_page.text
    assert second_page.status_code == 200
    assert "file-000.CSV" in second_page.text
    assert "issue-000" in second_page.text
