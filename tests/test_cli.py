from pathlib import Path

from cm_dashboard import cli
from cm_dashboard.importing.validation import ValidationIssue


def test_cli_inspect_source_reports_source_counts(tmp_path: Path, capsys) -> None:
    (tmp_path / "SOLD ARTICLES-BYPURCHASEDATE-2026-01-01_2026-01-31.CSV").write_text(
        "placeholder"
    )
    (tmp_path / "README.md").write_text("ignored")

    exit_code = cli.main(["inspect-source", "--source", str(tmp_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "valid files: 1" in output
    assert "CSV: 1" in output


def test_cli_import_wires_arguments_to_pipeline(tmp_path: Path, monkeypatch, capsys) -> None:
    calls = {}

    def fake_create_database(database_path):
        calls["db"] = database_path
        return "connection"

    def fake_import_source_folder(connection, source_path):
        calls["connection"] = connection
        calls["source"] = source_path
        return ("one", "two")

    monkeypatch.setattr(cli, "create_database", fake_create_database)
    monkeypatch.setattr(cli, "import_source_folder", fake_import_source_folder)

    exit_code = cli.main(
        ["import", "--source", str(tmp_path / "source"), "--db", str(tmp_path / "db.sqlite")]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls["db"] == (tmp_path / "db.sqlite").resolve(strict=False)
    assert calls["source"] == (tmp_path / "source").resolve(strict=False)
    assert calls["connection"] == "connection"
    assert "imported files: 2" in output


def test_cli_validate_wires_database_to_validation(tmp_path: Path, monkeypatch, capsys) -> None:
    calls = {}

    def fake_connect_database(database_path):
        calls["db"] = database_path
        return "connection"

    def fake_validate_database(connection):
        calls["connection"] = connection
        return (
            ValidationIssue(
                severity="warning",
                code="example",
                message="example warning",
            ),
        )

    monkeypatch.setattr(cli, "connect_database", fake_connect_database)
    monkeypatch.setattr(cli, "validate_database", fake_validate_database)

    exit_code = cli.main(["validate", "--db", str(tmp_path / "db.sqlite")])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls["db"] == (tmp_path / "db.sqlite").resolve(strict=False)
    assert calls["connection"] == "connection"
    assert "issues: 1" in output
    assert "warning: example: example warning" in output
