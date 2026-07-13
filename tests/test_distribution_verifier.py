import zipfile

import pytest

from scripts.verify_distribution import (
    REQUIRED_WHEEL_FILES,
    REQUIRED_WHEEL_SUFFIXES,
    verify_distribution,
)


def test_distribution_verifier_accepts_complete_wheel(tmp_path) -> None:
    wheel = tmp_path / "cm_dashboard-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for path in REQUIRED_WHEEL_FILES:
            archive.writestr(path, "fixture")
        for suffix in REQUIRED_WHEEL_SUFFIXES:
            archive.writestr(f"cm_dashboard-1.0.0{suffix}", "fixture")

    assert verify_distribution(tmp_path) == wheel


def test_distribution_verifier_rejects_missing_runtime_resources(tmp_path) -> None:
    wheel = tmp_path / "cm_dashboard-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("cm_dashboard/__init__.py", "")

    with pytest.raises(RuntimeError, match="missing runtime resources"):
        verify_distribution(tmp_path)
