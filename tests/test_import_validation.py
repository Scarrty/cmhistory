from cm_dashboard.db import create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.pipeline import import_source_file, import_source_folder
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.importing.validation import (
    persist_validation_issues,
    refresh_validation_issues,
    validate_database,
    validate_source_folder,
)
from tests.fixtures import require_fixture_path, source_root
from tests.synthetic_sources import write_article_source, write_shipment_source


def test_validate_source_folder_reports_known_missing_coverage_examples() -> None:
    issues = validate_source_folder(source_root(), check_headers=False)
    missing = {
        (
            issue.direction,
            issue.entity,
            issue.date_basis,
            issue.period_start.isoformat() if issue.period_start else None,
            issue.period_end.isoformat() if issue.period_end else None,
        )
        for issue in issues
        if issue.code == "missing_period_coverage"
    }

    assert ("PURCHASED", "ARTICLES", "PURCHASEDATE", "2024-06-01", "2024-06-30") in missing
    assert ("SOLD", "ARTICLES", "PURCHASEDATE", "2019-01-01", "2019-01-31") in missing
    assert ("SOLD", "SHIPMENTS", "PAYMENTDATE", "2025-08-01", "2025-08-31") in missing


def test_validate_database_reports_duplicates_unmatched_and_grouping_summary(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    for key in ("sold_articles_2026_01_csv", "sold_articles_2026_01_xls", "unicode_shipment"):
        path = require_fixture_path(key)
        import_source_file(
            connection,
            SourceFile(path=path, metadata=require_parsed_filename(path)),
        )

    issues = validate_database(connection)
    codes = {issue.code for issue in issues}

    assert "duplicate_article_source_overlap" in codes
    assert "unmatched_article_order" in codes
    assert "shipment_grouping_summary" in codes


def test_persist_validation_issues_stores_issues(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    issues = validate_source_folder(source_root(), check_headers=False)

    stored_count = persist_validation_issues(connection, issues[:3])

    assert stored_count == 3
    assert connection.execute("SELECT COUNT(*) FROM import_issues").fetchone()[0] == 3


def test_refresh_validation_issues_is_repeatable_and_preserves_import_failures(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    path = require_fixture_path("unicode_shipment")
    result = import_source_file(
        connection,
        SourceFile(path=path, metadata=require_parsed_filename(path)),
    )
    connection.execute(
        """
        INSERT INTO import_issues (import_file_id, severity, code, message)
        VALUES (?, 'error', 'import_failed', 'preserve me')
        """,
        (result.import_file_id,),
    )
    connection.commit()

    first_count = refresh_validation_issues(connection)
    second_count = refresh_validation_issues(connection)

    assert first_count == second_count
    assert connection.execute(
        "SELECT COUNT(*) FROM import_issues WHERE code = 'import_failed'"
    ).fetchone()[0] == 1
    derived_count = connection.execute(
        "SELECT COUNT(*) FROM import_issues WHERE code != 'import_failed'"
    ).fetchone()[0]
    assert derived_count == second_count


def test_validation_reports_article_and_shipment_total_mismatches(tmp_path) -> None:
    source = tmp_path / "source"
    write_article_source(
        source / "PURCHASED ARTICLES-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV",
        overrides={"Amount": "2", "Total": "16.0"},
    )
    write_shipment_source(
        source / "PURCHASED SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.CSV",
        overrides={"Total Value": "10.5"},
    )
    connection = create_database(tmp_path / "cardmarket.db")

    import_source_folder(connection, source)

    codes = {
        row["code"] for row in connection.execute("SELECT code FROM import_issues").fetchall()
    }
    assert "article_shipment_mismatch" in codes
    assert "shipment_total_mismatch" in codes
