from pathlib import Path


def test_verify_mvp_script_documents_expected_commands() -> None:
    script_path = Path("scripts/verify_mvp.ps1")

    assert script_path.is_file()
    script = script_path.read_text(encoding="utf-8")
    assert 'CM_DASHBOARD_RUN_FULL_SOURCE_TESTS = "1"' in script
    assert '"-m", "pytest", "-q"' in script
    assert '"-m", "ruff", "check", "src", "tests", "scripts"' in script
    assert '"-m", "mypy"' in script
    assert '"-m", "pip", "check"' in script
    assert '"-m", "pip_audit"' in script
    assert '"-m", "build"' in script
    assert '"scripts/verify_distribution.py", "--dist", "dist"' in script
    assert "$LASTEXITCODE -ne 0" in script
    assert "inspect-source" in script
    assert '"rebuild", "--source"' in script
    assert '"validate", "--db"' in script
    assert "data\\verify_mvp.db" in script
