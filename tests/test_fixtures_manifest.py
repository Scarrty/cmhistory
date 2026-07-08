from tests.fixtures import FIXTURES, missing_fixture_keys, require_fixture_path


def test_fixture_manifest_contains_required_regression_sources() -> None:
    assert {
        "tolerant_xls",
        "unicode_shipment",
        "sold_articles_2026_01_csv",
        "sold_articles_2026_01_xls",
        "purchased_missing_2024_06_payment_articles",
        "sold_missing_2019_01_payment_articles",
        "sold_missing_2025_08_purchase_articles",
    }.issubset(FIXTURES)


def test_required_source_fixtures_exist_or_skip_with_clear_message() -> None:
    missing = missing_fixture_keys()
    if missing:
        require_fixture_path(missing[0])

    for key in FIXTURES:
        assert require_fixture_path(key).is_file()
