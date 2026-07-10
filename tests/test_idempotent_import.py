import pytest

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import SourceFileChangedError, import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from tests.fixtures import require_fixture_path
from tests.synthetic_sources import write_article_source


def test_reimporting_same_files_does_not_duplicate_normalized_facts(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    article_source = _source_file("tolerant_xls")
    shipment_source = _source_file("unicode_shipment")

    first_article = import_source_file(connection, article_source)
    first_shipment = import_source_file(connection, shipment_source)
    first_counts = _fact_counts(connection)

    second_article = import_source_file(connection, article_source)
    second_shipment = import_source_file(connection, shipment_source)
    second_counts = _fact_counts(connection)

    assert first_article.status == first_shipment.status == "imported"
    assert second_article.status == second_shipment.status == "skipped"
    assert second_counts == first_counts


def test_changed_source_path_requires_explicit_rebuild_without_mixing_facts(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    path = tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.CSV"
    write_article_source(path)
    source_file = SourceFile(path=path, metadata=_metadata(path))
    import_source_file(connection, source_file)
    counts_before = _fact_counts(connection)

    write_article_source(path, overrides={"Total": "9.0"})

    with pytest.raises(SourceFileChangedError, match="rebuild"):
        import_source_file(connection, source_file)

    assert _fact_counts(connection) == counts_before
    import_file = connection.execute("SELECT * FROM import_files").fetchone()
    assert import_file["import_status"] == "conflict"
    assert connection.execute("SELECT code FROM import_issues").fetchone()["code"] == (
        "source_file_changed"
    )


def _source_file(key: str) -> SourceFile:
    from cm_dashboard.importing.filename import require_parsed_filename

    path = require_fixture_path(key)
    return SourceFile(path=path, metadata=require_parsed_filename(path))


def _metadata(path):
    from cm_dashboard.importing.filename import require_parsed_filename

    return require_parsed_filename(path)


def _fact_counts(connection) -> dict[str, int]:
    tables = [
        "import_files",
        "raw_article_rows",
        "raw_shipment_rows",
        "shipments",
        "shipment_events",
        "products",
        "product_labels",
        "expansions",
        "categories",
        "article_lines",
    ]
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in tables
    }
