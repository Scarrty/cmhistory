from datetime import date, datetime
from decimal import Decimal

import pytest

from cm_dashboard.importing.normalize import (
    normalize_bool,
    normalize_currency,
    normalize_date,
    normalize_datetime,
    normalize_decimal,
    normalize_identifier,
    normalize_int,
    normalize_text,
)


def test_normalize_text_trims_and_converts_empty_to_none() -> None:
    assert normalize_text("  Magic Lot  ") == "Magic Lot"
    assert normalize_text("") is None
    assert normalize_text(None) is None


def test_normalize_identifier_removes_xls_float_suffix() -> None:
    assert normalize_identifier(12345678.0) == "12345678"
    assert normalize_identifier(" 1234567890 ") == "1234567890"


def test_normalize_int_accepts_numeric_strings_and_xls_floats() -> None:
    assert normalize_int("2") == 2
    assert normalize_int(2.0) == 2
    assert normalize_int(Decimal("2")) == 2


def test_normalize_int_rejects_fractional_values() -> None:
    with pytest.raises(ValueError):
        normalize_int("2.5")


def test_normalize_decimal_accepts_european_and_dot_decimal_values() -> None:
    assert normalize_decimal("39,60") == Decimal("39.60")
    assert normalize_decimal("1.5") == Decimal("1.5")
    assert normalize_decimal(19.8) == Decimal("19.8")
    assert normalize_decimal("") is None


def test_normalize_decimal_handles_thousands_separators() -> None:
    assert normalize_decimal("1.234,56") == Decimal("1234.56")
    assert normalize_decimal("1,234.56") == Decimal("1234.56")


def test_normalize_datetime_accepts_cardmarket_text_formats() -> None:
    assert normalize_datetime("2026-01-17 07:18:03") == datetime(2026, 1, 17, 7, 18, 3)
    assert normalize_datetime("11/06/2016 21:52") == datetime(2016, 6, 11, 21, 52)


def test_normalize_datetime_accepts_excel_serial_values() -> None:
    assert normalize_datetime(42539) == datetime(2016, 6, 18)
    parsed = normalize_datetime(42539.792013889)

    assert parsed is not None
    assert parsed.date() == date(2016, 6, 18)
    assert parsed.hour == 19
    assert parsed.minute == 0


def test_normalize_date_returns_date_only() -> None:
    assert normalize_date("2026-01-17 07:18:03") == date(2026, 1, 17)


def test_normalize_bool_accepts_cardmarket_professional_marker() -> None:
    assert normalize_bool("X") is True
    assert normalize_bool("") is False
    assert normalize_bool("0") is False


def test_normalize_currency_uppercases_currency_codes() -> None:
    assert normalize_currency(" eur ") == "EUR"
    assert normalize_currency("") is None
