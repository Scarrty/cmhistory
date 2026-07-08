from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.readers import read_spreadsheet
from cm_dashboard.importing.schemas import HeaderIssueKind, schema_for, validate_headers
from tests.fixtures import require_fixture_path


def test_article_schema_matches_payment_fixture_headers() -> None:
    path = require_fixture_path("tolerant_xls")
    metadata = require_parsed_filename(path)
    sheet = read_spreadsheet(path)

    result = validate_headers(sheet.headers, metadata)

    assert result.is_compatible
    assert result.issues == ()
    assert result.schema.columns == sheet.headers


def test_purchased_shipment_schema_matches_fixture_headers() -> None:
    path = require_fixture_path("unicode_shipment")
    metadata = require_parsed_filename(path)
    sheet = read_spreadsheet(path)

    result = validate_headers(sheet.headers, metadata)

    assert result.is_compatible
    assert result.issues == ()
    assert "Trustee service fee" in result.schema.columns
    assert "Commission" not in result.schema.columns


def test_sold_shipment_schema_uses_commission_column() -> None:
    metadata = require_parsed_filename(
        "SOLD SHIPMENTS-BYPAYMENTDATE-2026-01-01_2026-01-31.XLS"
    )

    schema = schema_for(metadata)

    assert "Commission" in schema.columns
    assert "Trustee service fee" not in schema.columns


def test_validation_reports_missing_and_extra_columns_without_crashing() -> None:
    metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )
    headers = (
        "Shipment nr.",
        "Date of purchase",
        "Article",
        "Product ID",
        "Localized Product Name",
        "Expansion",
        "Category",
        "Amount",
        "Article Value",
        "Total",
        "Comments",
        "Unexpected Column",
    )

    result = validate_headers(headers, metadata)

    assert not result.is_compatible
    assert {issue.kind for issue in result.issues} == {
        HeaderIssueKind.MISSING,
        HeaderIssueKind.EXTRA,
    }
    assert any(issue.column == "Currency" for issue in result.issues)
    assert any(issue.column == "Unexpected Column" for issue in result.issues)


def test_validation_reports_duplicate_columns_without_crashing() -> None:
    metadata = require_parsed_filename(
        "PURCHASED ARTICLES-BYPAYMENTDATE-2026-01-01_2026-01-31.XLS"
    )
    schema = schema_for(metadata)
    headers = schema.columns + ("Currency",)

    result = validate_headers(headers, metadata)

    assert not result.is_compatible
    assert any(issue.kind == HeaderIssueKind.DUPLICATE for issue in result.issues)
