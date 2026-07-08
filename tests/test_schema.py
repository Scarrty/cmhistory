import sqlite3

from cm_dashboard.db import apply_migrations, connect_database, create_database


REQUIRED_TABLES = {
    "schema_migrations",
    "import_files",
    "raw_article_rows",
    "raw_shipment_rows",
    "shipments",
    "shipment_events",
    "article_lines",
    "products",
    "product_labels",
    "expansions",
    "categories",
    "import_issues",
}


def test_create_database_runs_initial_schema(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")

    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert REQUIRED_TABLES.issubset(tables)


def test_initial_schema_has_required_indexes(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")

    indexes = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    }

    assert {
        "idx_import_files_context",
        "idx_raw_article_rows_order_id",
        "idx_raw_shipment_rows_resolved_order_id",
        "idx_article_lines_filters",
        "idx_import_issues_file_severity",
    }.issubset(indexes)


def test_migrations_are_idempotent(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")

    apply_migrations(connection)

    applied = connection.execute("SELECT migration_id FROM schema_migrations").fetchall()
    assert [row["migration_id"] for row in applied] == ["001_init.sql"]


def test_connections_enable_foreign_keys() -> None:
    connection = connect_database(":memory:")

    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_foreign_keys_are_enforced_after_migration(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")

    try:
        connection.execute(
            """
            INSERT INTO raw_article_rows (
                import_file_id, source_row_number, raw_values_json
            ) VALUES (999, 2, '{}')
            """
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("Expected foreign key constraint to reject missing import_file")
