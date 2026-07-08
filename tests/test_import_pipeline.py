import pytest

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from tests.fixtures import require_fixture_path


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


def __import_metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)
