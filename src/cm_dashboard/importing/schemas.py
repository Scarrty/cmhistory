"""Expected source headers for Cardmarket export families."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cm_dashboard.importing.filename import DateBasis, Direction, ExportEntity, ParsedFilename


class HeaderIssueKind(StrEnum):
    MISSING = "missing"
    EXTRA = "extra"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class HeaderIssue:
    kind: HeaderIssueKind
    column: str
    message: str


@dataclass(frozen=True)
class HeaderSchema:
    name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class HeaderValidationResult:
    schema: HeaderSchema
    headers: tuple[str, ...]
    issues: tuple[HeaderIssue, ...]

    @property
    def is_compatible(self) -> bool:
        return not any(
            issue.kind in {HeaderIssueKind.MISSING, HeaderIssueKind.DUPLICATE}
            for issue in self.issues
        )


ARTICLE_BASE_COLUMNS = (
    "Shipment nr.",
    "{date_column}",
    "Article",
    "Product ID",
    "Localized Product Name",
    "Expansion",
    "Category",
    "Amount",
    "Article Value",
    "Total",
    "Currency",
    "Comments",
)

SHIPMENT_BASE_COLUMNS = (
    "OrderID",
    "Username",
    "Name",
    "Street",
    "City",
    "Country",
    "Is Professional",
    "VAT Number",
    "{date_column}",
    "Article Count",
    "Merchandise Value",
    "Shipment Costs",
    "{fee_column}",
    "Total Value",
    "Currency",
    "Description",
    "Product ID",
    "Localized Product Name",
)


def schema_for(metadata: ParsedFilename) -> HeaderSchema:
    if metadata.entity == ExportEntity.ARTICLES:
        return HeaderSchema(
            name=f"{metadata.direction.value} ARTICLES {metadata.date_basis.value}",
            columns=_format_columns(
                ARTICLE_BASE_COLUMNS,
                date_column=_article_date_column(metadata.date_basis),
            ),
        )

    return HeaderSchema(
        name=f"{metadata.direction.value} SHIPMENTS {metadata.date_basis.value}",
        columns=_format_columns(
            SHIPMENT_BASE_COLUMNS,
            date_column=_shipment_date_column(metadata.date_basis),
            fee_column=_shipment_fee_column(metadata.direction),
        ),
    )


def validate_headers(headers: tuple[str, ...], metadata: ParsedFilename) -> HeaderValidationResult:
    schema = schema_for(metadata)
    issues: list[HeaderIssue] = []

    expected_set = set(schema.columns)
    observed_set = set(headers)
    for column in schema.columns:
        if column not in observed_set:
            issues.append(
                HeaderIssue(
                    kind=HeaderIssueKind.MISSING,
                    column=column,
                    message=f"Missing expected column: {column}",
                )
            )

    for column in headers:
        if column not in expected_set:
            issues.append(
                HeaderIssue(
                    kind=HeaderIssueKind.EXTRA,
                    column=column,
                    message=f"Unexpected source column: {column}",
                )
            )

    seen: set[str] = set()
    for column in headers:
        if column in seen:
            issues.append(
                HeaderIssue(
                    kind=HeaderIssueKind.DUPLICATE,
                    column=column,
                    message=f"Duplicate source column: {column}",
                )
            )
        seen.add(column)

    return HeaderValidationResult(schema=schema, headers=headers, issues=tuple(issues))


def _format_columns(columns: tuple[str, ...], **values: str) -> tuple[str, ...]:
    return tuple(column.format(**values) for column in columns)


def _article_date_column(date_basis: DateBasis) -> str:
    return "Date of purchase" if date_basis == DateBasis.PURCHASEDATE else "Date of payment"


def _shipment_date_column(date_basis: DateBasis) -> str:
    return "Date of Purchase" if date_basis == DateBasis.PURCHASEDATE else "Date of Payment"


def _shipment_fee_column(direction: Direction) -> str:
    return "Trustee service fee" if direction == Direction.PURCHASED else "Commission"
