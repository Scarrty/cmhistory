from datetime import date
from pathlib import Path

from cm_dashboard.importing.filename import (
    DateBasis,
    Direction,
    ExportEntity,
    FileExtension,
    parse_filename,
    require_parsed_filename,
)


def test_parse_purchased_articles_by_payment_date_xls_filename() -> None:
    result = parse_filename("PURCHASED ARTICLES-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS")

    assert result.ok
    assert result.metadata is not None
    assert result.metadata.direction == Direction.PURCHASED
    assert result.metadata.entity == ExportEntity.ARTICLES
    assert result.metadata.date_basis == DateBasis.PAYMENTDATE
    assert result.metadata.file_extension == FileExtension.XLS
    assert result.metadata.period_start == date(2016, 6, 1)
    assert result.metadata.period_end == date(2016, 6, 30)


def test_parse_sold_shipments_by_purchase_date_xls_filename_from_path() -> None:
    metadata = require_parsed_filename(
        Path("folder") / "SOLD SHIPMENTS-BYPURCHASEDATE-2026-06-01_2026-06-30.XLS"
    )

    assert metadata.direction == Direction.SOLD
    assert metadata.entity == ExportEntity.SHIPMENTS
    assert metadata.date_basis == DateBasis.PURCHASEDATE
    assert metadata.period_start == date(2026, 6, 1)
    assert metadata.period_end == date(2026, 6, 30)


def test_parse_csv_filename() -> None:
    metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )

    assert metadata.file_extension == FileExtension.CSV
    assert metadata.entity == ExportEntity.ARTICLES


def test_parse_xlsx_filename_for_future_exports() -> None:
    metadata = require_parsed_filename(
        "PURCHASED SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.XLSX"
    )

    assert metadata.file_extension == FileExtension.XLSX
    assert metadata.direction == Direction.PURCHASED


def test_invalid_filename_returns_structured_issue() -> None:
    result = parse_filename("README.md")

    assert not result.ok
    assert result.metadata is None
    assert result.issue is not None
    assert result.issue.file_name == "README.md"
    assert "Expected" in result.issue.message


def test_period_end_before_start_returns_structured_issue() -> None:
    result = parse_filename("SOLD ARTICLES-BYPAYMENTDATE-2026-02-01_2026-01-31.XLS")

    assert not result.ok
    assert result.issue is not None
    assert "Period end" in result.issue.message


def test_require_parsed_filename_raises_for_invalid_filename() -> None:
    try:
        require_parsed_filename("invalid.xls")
    except ValueError as exc:
        assert "Expected" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
