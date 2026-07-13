import tomllib
from pathlib import Path

from cm_dashboard import __version__


def test_package_and_project_versions_match() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert __version__ == "1.0.0"
    assert project["project"]["version"] == __version__
    assert "100% AI-generated" in project["project"]["description"]
