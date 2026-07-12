"""Raw spreadsheet readers for Cardmarket exports."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from python_calamine import CalamineWorkbook


@dataclass(frozen=True)
class WorksheetData:
    path: Path
    sheet_name: str
    headers: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]

    @property
    def row_count(self) -> int:
        return len(self.rows)


def read_spreadsheet(path: str | Path) -> WorksheetData:
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(source_path)
    if suffix in {".xls", ".xlsx"}:
        return _read_excel(source_path)
    raise ValueError(f"Unsupported spreadsheet extension: {source_path.suffix}")


def _read_excel(path: Path) -> WorksheetData:
    workbook = CalamineWorkbook.from_path(path)
    if not workbook.sheet_names:
        raise ValueError(f"Workbook has no sheets: {path}")

    sheet = workbook.get_sheet_by_index(0)
    values = sheet.to_python(skip_empty_area=False)
    headers = _normalize_headers(values[0] if values else [])
    rows = tuple(
        _pad_row(row, len(headers), row_number=row_number)
        for row_number, row in enumerate(values[1:], start=2)
        if not _is_blank_row(row)
    )
    return WorksheetData(
        path=path.resolve(strict=False),
        sheet_name=sheet.name,
        headers=headers,
        rows=rows,
    )


def _read_csv(path: Path) -> WorksheetData:
    text = _read_csv_text(path)
    sample = text[:4096]
    delimiter = _detect_csv_delimiter(sample)
    # io.StringIO keeps line endings, so csv.reader can reassemble quoted
    # fields that span multiple lines without dropping the embedded newline.
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        raw_headers = next(reader)
    except StopIteration:
        raw_headers = []

    headers = _normalize_headers(raw_headers)
    rows = tuple(
        _pad_row(row, len(headers), row_number=row_number)
        for row_number, row in enumerate(reader, start=2)
        if not _is_blank_row(row)
    )
    return WorksheetData(
        path=path.resolve(strict=False),
        sheet_name="CSV",
        headers=headers,
        rows=rows,
    )


def _read_csv_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text()


def _detect_csv_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        return ";" if sample.count(";") >= sample.count(",") else ","


def _normalize_headers(values: Sequence[Any]) -> tuple[str, ...]:
    return tuple("" if value is None else str(value).strip() for value in values)


def _pad_row(values: Sequence[Any], expected_length: int, *, row_number: int) -> tuple[Any, ...]:
    if len(values) > expected_length:
        extra_values = values[expected_length:]
        if any(str(value).strip() != "" for value in extra_values):
            raise ValueError(
                f"Row {row_number} has {len(values)} cells but only "
                f"{expected_length} header columns"
            )
        return tuple(values[:expected_length])
    if len(values) == expected_length:
        return tuple(values)
    return tuple(values) + ("",) * (expected_length - len(values))


def _is_blank_row(values: Sequence[Any]) -> bool:
    return all(str(value).strip() == "" for value in values)
