"""Helpers for referencing private local source fixtures without copying them."""

import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from cm_dashboard.config import normalize_path

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ROOT_ENV = "CM_DASHBOARD_SOURCE_ROOT"
FULL_SOURCE_TESTS_ENV = "CM_DASHBOARD_RUN_FULL_SOURCE_TESTS"

requires_full_source = pytest.mark.skipif(
    os.environ.get(FULL_SOURCE_TESTS_ENV) != "1",
    reason=(
        f"Set {FULL_SOURCE_TESTS_ENV}=1 to run tests that assert the "
        "private full source folder inventory."
    ),
)


@dataclass(frozen=True)
class SourceFixture:
    key: str
    relative_path: str
    purpose: str


FIXTURES: dict[str, SourceFixture] = {
    "tolerant_xls": SourceFixture(
        key="tolerant_xls",
        relative_path="PURCHASED ARTICLES-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS",
        purpose="XLS parser tolerance fixture",
    ),
    "unicode_shipment": SourceFixture(
        key="unicode_shipment",
        relative_path="PURCHASED SHIPMENTS-BYPAYMENTDATE-2016-06-01_2016-06-30.XLS",
        purpose="Unicode fidelity and grouped shipment rows",
    ),
    "sold_articles_2026_01_csv": SourceFixture(
        key="sold_articles_2026_01_csv",
        relative_path="SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV",
        purpose="CSV side of known duplicate CSV/XLS pair",
    ),
    "sold_articles_2026_01_xls": SourceFixture(
        key="sold_articles_2026_01_xls",
        relative_path="SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.XLS",
        purpose="XLS side of known duplicate CSV/XLS pair",
    ),
    "purchased_missing_2024_06_payment_articles": SourceFixture(
        key="purchased_missing_2024_06_payment_articles",
        relative_path="PURCHASED ARTICLES-BYPAYMENTDATE-2024-06-01_2024-06-30.XLS",
        purpose="Missing purchase-date coverage comparison",
    ),
    "sold_missing_2019_01_payment_articles": SourceFixture(
        key="sold_missing_2019_01_payment_articles",
        relative_path="SOLD ARTICLES-BYPAYMENTDATE-2019-01-01_2019-01-31.XLS",
        purpose="Sold coverage gap comparison",
    ),
    "sold_missing_2025_08_purchase_articles": SourceFixture(
        key="sold_missing_2025_08_purchase_articles",
        relative_path="SOLD ARTICLES-BYPURCHASEDATE-2025-08-01_2025-08-31.XLS",
        purpose="Sold purchase-date coverage gap comparison",
    ),
    "charizard_2016_payment_articles": SourceFixture(
        key="charizard_2016_payment_articles",
        relative_path="PURCHASED ARTICLES-BYPAYMENTDATE-2016-10-01_2016-10-31.XLS",
        purpose="Product detail localized label fixture with Charizard label",
    ),
    "charizard_2020_payment_articles": SourceFixture(
        key="charizard_2020_payment_articles",
        relative_path="PURCHASED ARTICLES-BYPAYMENTDATE-2020-04-01_2020-04-30.XLS",
        purpose="Product detail localized label fixture with Glurak label",
    ),
}


def source_root() -> Path:
    configured_root = os.environ.get(SOURCE_ROOT_ENV)
    if configured_root:
        return normalize_path(configured_root)
    return REPO_ROOT


def fixture_path(key: str) -> Path:
    fixture = FIXTURES[key]
    return source_root() / fixture.relative_path


def missing_fixture_keys() -> list[str]:
    return [key for key in FIXTURES if not fixture_path(key).is_file()]


def require_fixture_path(key: str) -> Path:
    path = fixture_path(key)
    if not path.is_file():
        pytest.skip(f"Source fixture {key!r} is missing at {path}")
    return path
