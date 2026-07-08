from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from tests.fixtures import require_fixture_path


def test_reimporting_same_files_does_not_duplicate_normalized_facts(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    article_source = _source_file("tolerant_xls")
    shipment_source = _source_file("unicode_shipment")

    import_source_file(connection, article_source)
    import_source_file(connection, shipment_source)
    first_counts = _fact_counts(connection)

    import_source_file(connection, article_source)
    import_source_file(connection, shipment_source)
    second_counts = _fact_counts(connection)

    assert second_counts == first_counts


def _source_file(key: str) -> SourceFile:
    from cm_dashboard.importing.filename import require_parsed_filename

    path = require_fixture_path(key)
    return SourceFile(path=path, metadata=require_parsed_filename(path))


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
