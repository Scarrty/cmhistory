from pathlib import Path

from cm_dashboard.importing.deduplication import (
    article_business_key,
    article_business_key_string,
    article_business_key_strings,
    article_business_keys,
)
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.readers import WorksheetData, read_spreadsheet
from tests.fixtures import require_fixture_path, source_root


def test_known_csv_xls_duplicate_pair_produces_matching_article_business_keys() -> None:
    csv_path = require_fixture_path("sold_articles_2026_01_csv")
    xls_path = require_fixture_path("sold_articles_2026_01_xls")
    csv_sheet = read_spreadsheet(csv_path)
    xls_sheet = read_spreadsheet(xls_path)

    csv_keys = set(article_business_keys(csv_sheet, require_parsed_filename(csv_path)))
    xls_keys = set(article_business_keys(xls_sheet, require_parsed_filename(xls_path)))

    assert len(csv_keys) == csv_sheet.row_count == 20
    assert len(xls_keys) == xls_sheet.row_count == 20
    assert csv_keys == xls_keys


def test_all_known_csv_xls_pairs_produce_matching_serialized_business_keys() -> None:
    for month in range(1, 6):
        stem = f"SOLD ARTICLES-BYPURCHASEDATE-2026-{month:02d}-01_2026-{month:02d}"
        period_end = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31}[month]
        stem = f"{stem}-{period_end:02d}"
        csv_path = source_root() / f"{stem}.CSV"
        xls_path = source_root() / f"{stem}.XLS"
        if not csv_path.is_file() or not xls_path.is_file():
            continue

        csv_keys = article_business_key_strings(
            read_spreadsheet(csv_path), require_parsed_filename(csv_path)
        )
        xls_keys = article_business_key_strings(
            read_spreadsheet(xls_path), require_parsed_filename(xls_path)
        )

        assert csv_keys == xls_keys


def test_article_business_key_normalizes_csv_and_xls_row_shapes() -> None:
    csv_metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )
    xls_metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.XLS"
    )
    csv_row = {
        "Shipment nr.": "1000001",
        "Date of purchase": "2026-01-17 07:18:03",
        "Article": "Wally's Compassion",
        "Product ID": "851247",
        "Localized Product Name": "Heikos Mitgefuhl",
        "Expansion": "Mega Evolution",
        "Category": "Pokemon Single",
        "Amount": "1",
        "Article Value": "1.50",
        "Total": "1,50",
        "Currency": "eur",
        "Comments": " A026 ",
    }
    xls_row = {
        "Shipment nr.": 1000001.0,
        "Date of purchase": "17/01/2026 7:18",
        "Article": "Wally's Compassion",
        "Product ID": 851247.0,
        "Localized Product Name": "Heikos Mitgefuhl",
        "Expansion": "Mega Evolution",
        "Category": "Pokemon Single",
        "Amount": 1.0,
        "Article Value": 1.5,
        "Total": 1.5,
        "Currency": "EUR",
        "Comments": "A026",
    }

    assert article_business_key(csv_row, csv_metadata) == article_business_key(
        xls_row, xls_metadata
    )


def test_serialized_business_key_canonicalizes_decimal_scale() -> None:
    metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )
    integer_scale = _synthetic_row(article_value="8", total="8.00")
    decimal_scale = _synthetic_row(article_value="8.0", total=8.0)

    assert article_business_key_string(integer_scale, metadata) == article_business_key_string(
        decimal_scale, metadata
    )


def test_repeated_identical_rows_get_distinct_occurrence_keys() -> None:
    metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )
    row = _synthetic_row(article_value="8", total="8")
    headers = tuple(row)
    values = tuple(row.values())
    sheet = WorksheetData(
        path=Path("synthetic.csv"),
        sheet_name="CSV",
        headers=headers,
        rows=(values, values),
    )

    keys = article_business_keys(sheet, metadata)

    assert len(set(keys)) == 2
    assert [key.occurrence_index for key in keys] == [1, 2]


def _synthetic_row(*, article_value, total) -> dict:
    return {
        "Shipment nr.": "1000001",
        "Date of purchase": "2026-01-17 07:18:03",
        "Article": "Synthetic Card",
        "Product ID": "2000001",
        "Localized Product Name": "Synthetic Card",
        "Expansion": "Synthetic Set",
        "Category": "Synthetic Category",
        "Amount": "1",
        "Article Value": article_value,
        "Total": total,
        "Currency": "EUR",
        "Comments": "fixture",
    }
