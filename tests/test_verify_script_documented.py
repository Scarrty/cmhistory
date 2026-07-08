from pathlib import Path


def test_verify_mvp_script_documents_expected_commands() -> None:
    script_path = Path("scripts/verify_mvp.ps1")

    assert script_path.is_file()
    script = script_path.read_text(encoding="utf-8")
    assert "-m pytest" in script
    assert "-m ruff check src tests" in script
    assert "inspect-source" in script
    assert "import --source" in script
    assert "validate --db" in script
    assert "data\\verify_mvp.db" in script
