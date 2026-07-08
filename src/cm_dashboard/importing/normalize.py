"""Cell-value normalization for Cardmarket imports."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

EXCEL_EPOCH = datetime(1899, 12, 30)
DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y",
)


def is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def normalize_text(value: Any) -> str | None:
    if is_empty(value):
        return None
    text = str(value).strip()
    return text or None


def normalize_identifier(value: Any) -> str | None:
    if is_empty(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def normalize_int(value: Any) -> int | None:
    if is_empty(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError(f"Expected integer-compatible value, got {value!r}")
    decimal_value = normalize_decimal(value)
    if decimal_value is None:
        return None
    if decimal_value == decimal_value.to_integral_value():
        return int(decimal_value)
    raise ValueError(f"Expected integer-compatible value, got {value!r}")


def normalize_decimal(value: Any) -> Decimal | None:
    if is_empty(value):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))

    text = str(value).strip().replace(" ", "")
    if text == "":
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def normalize_datetime(value: Any) -> datetime | None:
    if is_empty(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, int | float):
        return EXCEL_EPOCH + timedelta(days=float(value))

    text = str(value).strip()
    for date_format in DATETIME_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime value: {value!r}")


def normalize_date(value: Any) -> date | None:
    parsed = normalize_datetime(value)
    return parsed.date() if parsed is not None else None


def normalize_bool(value: Any) -> bool | None:
    if is_empty(value):
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"x", "yes", "true", "1", "y"}:
        return True
    if text in {"no", "false", "0", "n"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def normalize_currency(value: Any) -> str | None:
    text = normalize_text(value)
    return text.upper() if text else None
