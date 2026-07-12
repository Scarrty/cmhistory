from pathlib import Path

from cm_dashboard.importing.filename import DateBasis, Direction, ExportEntity
from cm_dashboard.importing.source_scan import scan_source_files
from tests.fixtures import requires_full_source, source_root


def test_scan_finds_importable_files_and_ignores_documentation(tmp_path: Path) -> None:
    valid_file = tmp_path / "PURCHASED ARTICLES-BYPAYMENTDATE-2026-01-01_2026-01-31.XLS"
    valid_file.write_text("placeholder")
    (tmp_path / "README.md").write_text("not an export")
    (tmp_path / "OUTPUT").mkdir()
    (tmp_path / "OUTPUT" / "SOLD ARTICLES-BYPAYMENTDATE-2026-01-01_2026-01-31.XLS").write_text(
        "not scanned recursively"
    )

    report = scan_source_files(tmp_path)

    assert report.total_candidates == 1
    assert len(report.files) == 1
    assert report.files[0].path == valid_file.resolve(strict=False)
    assert report.files[0].metadata.direction == Direction.PURCHASED
    assert report.files[0].metadata.entity == ExportEntity.ARTICLES
    assert report.files[0].metadata.date_basis == DateBasis.PAYMENTDATE
    assert report.unknown_files == ()


def test_scan_reports_unknown_importable_filename(tmp_path: Path) -> None:
    unknown_file = tmp_path / "unknown-export.XLS"
    unknown_file.write_text("placeholder")

    report = scan_source_files(tmp_path)

    assert report.files == ()
    assert len(report.unknown_files) == 1
    assert report.unknown_files[0].path == unknown_file.resolve(strict=False)
    assert "Expected" in report.unknown_files[0].issue.message


def test_scan_missing_source_path_returns_unknown_issue(tmp_path: Path) -> None:
    report = scan_source_files(tmp_path / "missing")

    assert report.files == ()
    assert len(report.unknown_files) == 1
    assert "not a directory" in report.unknown_files[0].issue.message


@requires_full_source
def test_scan_current_source_folder_matches_review_inventory() -> None:
    report = scan_source_files(source_root())

    assert len(report.files) == 447
    assert report.unknown_files == ()
    assert report.extension_counts == {"XLS": 442, "CSV": 5}
