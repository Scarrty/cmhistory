import pytest

from cm_dashboard.db import connect_database, create_database
from cm_dashboard.importing.pipeline import (
    DatabaseRebuildRequiredError,
    ImportBatchError,
    database_requires_rebuild,
    import_source_folder,
    rebuild_database,
)
from cm_dashboard.importing.version import NORMALIZATION_VERSION
from tests.synthetic_sources import write_article_source, write_shipment_source


def test_legacy_normalization_requires_and_supports_atomic_rebuild(tmp_path) -> None:
    source = tmp_path / "source"
    write_article_source(
        source / "PURCHASED ARTICLES-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV"
    )
    write_shipment_source(
        source / "PURCHASED SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV"
    )
    database_path = tmp_path / "cardmarket.db"
    connection = create_database(database_path)
    import_source_folder(connection, source)
    connection.execute("UPDATE import_files SET normalization_version = 1")
    connection.commit()

    assert database_requires_rebuild(connection)
    with pytest.raises(DatabaseRebuildRequiredError):
        import_source_folder(connection, source)
    connection.close()

    results = rebuild_database(source, database_path)

    assert {result.status for result in results} == {"imported"}
    rebuilt = connect_database(database_path)
    assert not database_requires_rebuild(rebuilt)
    assert rebuilt.execute(
        "SELECT DISTINCT normalization_version FROM import_files"
    ).fetchone()[0] == NORMALIZATION_VERSION
    assert rebuilt.execute("SELECT COUNT(*) FROM article_lines").fetchone()[0] == 1
    assert rebuilt.execute("SELECT COUNT(*) FROM shipments").fetchone()[0] == 1
    rebuilt.close()


def test_failed_rebuild_leaves_existing_database_untouched(tmp_path) -> None:
    source = tmp_path / "source"
    write_article_source(
        source / "SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.CSV",
        overrides={"Total": "invalid"},
    )
    database_path = tmp_path / "cardmarket.db"
    existing = create_database(database_path)
    existing.execute("CREATE TABLE local_marker (value TEXT NOT NULL)")
    existing.execute("INSERT INTO local_marker VALUES ('preserved')")
    existing.commit()
    existing.close()

    with pytest.raises(ImportBatchError):
        rebuild_database(source, database_path)

    unchanged = connect_database(database_path)
    assert unchanged.execute("SELECT value FROM local_marker").fetchone()[0] == "preserved"
    unchanged.close()
