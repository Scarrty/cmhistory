"""Parsing for Cardmarket export filenames."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path


class Direction(StrEnum):
    PURCHASED = "PURCHASED"
    SOLD = "SOLD"


class ExportEntity(StrEnum):
    ARTICLES = "ARTICLES"
    SHIPMENTS = "SHIPMENTS"


class DateBasis(StrEnum):
    PURCHASEDATE = "PURCHASEDATE"
    PAYMENTDATE = "PAYMENTDATE"


class FileExtension(StrEnum):
    XLS = "XLS"
    XLSX = "XLSX"
    CSV = "CSV"


@dataclass(frozen=True)
class ParsedFilename:
    file_name: str
    file_extension: FileExtension
    direction: Direction
    entity: ExportEntity
    date_basis: DateBasis
    period_start: date
    period_end: date


@dataclass(frozen=True)
class FilenameParseIssue:
    file_name: str
    message: str


@dataclass(frozen=True)
class FilenameParseResult:
    metadata: ParsedFilename | None = None
    issue: FilenameParseIssue | None = None

    @property
    def ok(self) -> bool:
        return self.metadata is not None and self.issue is None


_FILENAME_PATTERN = re.compile(
    r"^(?P<direction>PURCHASED|SOLD) "
    r"(?P<entity>ARTICLES|SHIPMENTS)-BY"
    r"(?P<date_basis>PURCHASEDATE|PAYMENTDATE)-"
    r"(?P<period_start>\d{4}-\d{2}-\d{2})_"
    r"(?P<period_end>\d{4}-\d{2}-\d{2})"
    r"\.(?P<extension>XLSX|XLS|CSV)$",
    re.IGNORECASE,
)


def parse_filename(path: str | Path) -> FilenameParseResult:
    file_name = Path(path).name
    match = _FILENAME_PATTERN.match(file_name)
    if not match:
        return FilenameParseResult(
            issue=FilenameParseIssue(
                file_name=file_name,
                message=(
                    "Expected '<PURCHASED|SOLD> <ARTICLES|SHIPMENTS>-BY"
                    "<PURCHASEDATE|PAYMENTDATE>-YYYY-MM-DD_YYYY-MM-DD.<XLS|XLSX|CSV>'"
                ),
            )
        )

    groups = {key: value.upper() for key, value in match.groupdict().items()}
    try:
        period_start = date.fromisoformat(match.group("period_start"))
        period_end = date.fromisoformat(match.group("period_end"))
    except ValueError as exc:
        return FilenameParseResult(
            issue=FilenameParseIssue(file_name=file_name, message=f"Invalid period date: {exc}")
        )

    if period_end < period_start:
        return FilenameParseResult(
            issue=FilenameParseIssue(
                file_name=file_name,
                message="Period end must be on or after period start",
            )
        )

    return FilenameParseResult(
        metadata=ParsedFilename(
            file_name=file_name,
            file_extension=FileExtension(groups["extension"]),
            direction=Direction(groups["direction"]),
            entity=ExportEntity(groups["entity"]),
            date_basis=DateBasis(groups["date_basis"]),
            period_start=period_start,
            period_end=period_end,
        )
    )


def require_parsed_filename(path: str | Path) -> ParsedFilename:
    result = parse_filename(path)
    if result.metadata is None:
        issue = result.issue
        message = issue.message if issue else "Unknown filename parse error"
        raise ValueError(message)
    return result.metadata
