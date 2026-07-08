"""Raw spreadsheet readers for Cardmarket exports."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import xlrd


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
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(source_path)
    if suffix == ".xls":
        return _read_xls(source_path)
    raise ValueError(f"Unsupported spreadsheet extension: {source_path.suffix}")


def _read_xls(path: Path) -> WorksheetData:
    workbook = xlrd.open_workbook(path, ignore_workbook_corruption=True)
    if workbook.nsheets < 1:
        raise ValueError(f"Workbook has no sheets: {path}")

    sheet = workbook.sheet_by_index(0)
    headers = _normalize_headers(sheet.row_values(0) if sheet.nrows else [])
    rows = tuple(
        _pad_row(sheet.row_values(row_index), len(headers))
        for row_index in range(1, sheet.nrows)
        if not _is_blank_row(sheet.row_values(row_index))
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
    reader = csv.reader(text.splitlines(), delimiter=delimiter)
    try:
        raw_headers = next(reader)
    except StopIteration:
        raw_headers = []

    headers = _normalize_headers(raw_headers)
    rows = tuple(
        _pad_row(row, len(headers))
        for row in reader
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


def _normalize_headers(values: list[Any]) -> tuple[str, ...]:
    return tuple("" if value is None else str(value).strip() for value in values)


def _pad_row(values: list[Any], expected_length: int) -> tuple[Any, ...]:
    if len(values) >= expected_length:
        return tuple(values[:expected_length])
    return tuple(values) + ("",) * (expected_length - len(values))


def _is_blank_row(values: list[Any]) -> bool:
    return all(str(value).strip() == "" for value in values)
