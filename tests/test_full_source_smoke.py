import os

import pytest

from cm_dashboard.db import create_database
from cm_dashboard.importing.pipeline import import_source_folder
from cm_dashboard.importing.validation import validate_database
from tests.fixtures import source_root


@pytest.mark.skipif(
    os.environ.get("CM_DASHBOARD_RUN_FULL_SOURCE_TESTS") != "1",
    reason="Set CM_DASHBOARD_RUN_FULL_SOURCE_TESTS=1 to run the private full-source smoke test.",
)
def test_full_source_folder_imports_and_validates(tmp_path) -> None:
    connection = create_database(tmp_path / "cardmarket.db")

    results = import_source_folder(connection, source_root())
    issues = validate_database(connection)
    codes = {issue.code for issue in issues}

    assert len(results) == 447
    assert "shipment_grouping_summary" in codes
    assert not [issue for issue in issues if issue.severity == "error"]
