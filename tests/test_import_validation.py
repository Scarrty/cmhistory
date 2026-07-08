from cm_dashboard.db import create_database
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.pipeline import import_source_file
from cm_dashboard.importing.source_scan import SourceFile
from cm_dashboard.importing.validation import (
    persist_validation_issues,
    validate_database,
    validate_source_folder,
)
from tests.fixtures import require_fixture_path, source_root


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

    assert "duplicate_article_business_key" in codes
    assert "unmatched_article_order" in codes
    assert "shipment_grouping_summary" in codes


def test_persist_validation_issues_stores_issues(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")
    issues = validate_source_folder(source_root(), check_headers=False)

    stored_count = persist_validation_issues(connection, issues[:3])

    assert stored_count == 3
    assert connection.execute("SELECT COUNT(*) FROM import_issues").fetchone()[0] == 3
