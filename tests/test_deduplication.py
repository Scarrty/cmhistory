from cm_dashboard.importing.deduplication import article_business_key, article_business_keys
from cm_dashboard.importing.filename import require_parsed_filename
from cm_dashboard.importing.readers import read_spreadsheet
from tests.fixtures import require_fixture_path


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


def test_article_business_key_normalizes_csv_and_xls_row_shapes() -> None:
    csv_metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV"
    )
    xls_metadata = require_parsed_filename(
        "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.XLS"
    )
    csv_row = {
        "Shipment nr.": "1251705672",
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
        "Shipment nr.": 1251705672.0,
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

    assert article_business_key(csv_row, csv_metadata) == article_business_key(xls_row, xls_metadata)
