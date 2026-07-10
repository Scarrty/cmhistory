import pytest

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file, import_source_folder
from cm_dashboard.importing.source_scan import SourceFile
from tests.fixtures import require_fixture_path
from tests.synthetic_sources import write_article_source


def test_import_pipeline_imports_representative_article_and_shipment_files(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    article_path = require_fixture_path("tolerant_xls")
    shipment_path = require_fixture_path("unicode_shipment")

    article_result = import_source_file(
        connection,
        SourceFile(path=article_path, metadata=__import_metadata(article_path)),
    )
    shipment_result = import_source_file(
        connection,
        SourceFile(path=shipment_path, metadata=__import_metadata(shipment_path)),
    )

    assert article_result.raw_row_count == article_result.normalized_row_count
    assert shipment_result.raw_row_count > shipment_result.normalized_row_count
    assert connection.execute("SELECT COUNT(*) FROM import_files").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(*) FROM raw_article_rows").fetchone()[0] > 0
    assert connection.execute("SELECT COUNT(*) FROM raw_shipment_rows").fetchone()[0] > 0
    assert connection.execute("SELECT COUNT(*) FROM shipments").fetchone()[0] > 0
    assert connection.execute("SELECT COUNT(*) FROM article_lines").fetchone()[0] > 0
    assert connection.execute(
        "SELECT COUNT(*) FROM article_lines WHERE shipment_id IS NULL"
    ).fetchone()[0] == 0


def test_import_pipeline_does_not_write_database_when_reader_fails(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    missing_path = tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.XLS"

    with pytest.raises(FileNotFoundError):
        import_source_file(
            connection,
            SourceFile(path=missing_path, metadata=__import_metadata(missing_path)),
        )

    assert connection.execute("SELECT COUNT(*) FROM import_files").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM raw_article_rows").fetchone()[0] == 0


def test_import_pipeline_rolls_back_invalid_file_and_records_failure(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    path = write_article_source(
        tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.CSV",
        overrides={"Amount": "not-an-integer"},
    )

    with pytest.raises(ValueError, match="Invalid decimal value"):
        import_source_file(
            connection,
            SourceFile(path=path, metadata=__import_metadata(path)),
        )

    import_file = connection.execute("SELECT * FROM import_files").fetchone()
    assert import_file["import_status"] == "failed"
    assert import_file["imported_at"] is None
    assert connection.execute("SELECT COUNT(*) FROM raw_article_rows").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM article_lines").fetchone()[0] == 0
    assert connection.execute(
        "SELECT code FROM import_issues WHERE import_file_id = ?",
        (import_file["import_file_id"],),
    ).fetchone()["code"] == "import_failed"


def test_folder_import_continues_after_one_invalid_file(tmp_path) -> None:
    source = tmp_path / "source"
    write_article_source(
        source / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.CSV",
        overrides={"Total": "invalid"},
    )
    write_article_source(
        source / "SOLD ARTICLES-BYPURCHASEDATE-2026-09-01_2026-09-30.CSV"
    )
    connection = create_database(tmp_path / "cardmarket.db")

    results = import_source_folder(connection, source)

    assert [result.status for result in results] == ["failed", "imported"]
    assert connection.execute("SELECT COUNT(*) FROM article_lines").fetchone()[0] == 1
    assert connection.execute(
        "SELECT COUNT(*) FROM import_files WHERE import_status = 'failed'"
    ).fetchone()[0] == 1


def __import_metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
