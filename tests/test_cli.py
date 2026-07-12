from pathlib import Path

import cm_dashboard.cli as cli
from cm_dashboard.importing.pipeline import ImportBatchError, ImportResult
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

    class FakeConnection:
        closed = False

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()

    def fake_create_database(database_path):
        calls["db"] = database_path
        return fake_connection

    def fake_import_source_folder(connection, source_path):
        calls["connection"] = connection
        calls["source"] = source_path
        return (
            ImportResult(1, "one.csv", "ARTICLES", 1, 1),
            ImportResult(2, "two.csv", "ARTICLES", 1, 0, status="skipped"),
        )

    monkeypatch.setattr(cli, "create_database", fake_create_database)
    monkeypatch.setattr(cli, "import_source_folder", fake_import_source_folder)

    exit_code = cli.main(
        ["import", "--source", str(tmp_path / "source"), "--db", str(tmp_path / "db.sqlite")]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls["db"] == (tmp_path / "db.sqlite").resolve(strict=False)
    assert calls["source"] == (tmp_path / "source").resolve(strict=False)
    assert calls["connection"] is fake_connection
    assert fake_connection.closed
    assert "imported files: 1" in output
    assert "skipped files: 1" in output


def test_cli_validate_wires_database_to_validation(tmp_path: Path, monkeypatch, capsys) -> None:
    calls = {}

    class FakeConnection:
        closed = False

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()

    def fake_connect_database(database_path):
        calls["db"] = database_path
        return fake_connection

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
    assert calls["connection"] is fake_connection
    assert fake_connection.closed
    assert "issues: 1" in output
    assert "warning: example: example warning" in output


def test_cli_validate_fails_on_error_issues(tmp_path: Path, monkeypatch, capsys) -> None:
    class FakeConnection:
        def close(self):
            pass

    def fake_validate_database(connection):
        return (
            ValidationIssue(severity="warning", code="minor", message="warning"),
            ValidationIssue(severity="error", code="import_failed", message="broken file"),
        )

    monkeypatch.setattr(cli, "connect_database", lambda path: FakeConnection())
    monkeypatch.setattr(cli, "validate_database", fake_validate_database)

    exit_code = cli.main(["validate", "--db", str(tmp_path / "db.sqlite")])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "error: import_failed: broken file" in output


def test_cli_rebuild_reports_failed_files_without_traceback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    def fake_rebuild_database(source_path, database_path):
        raise ImportBatchError(
            "Database rebuild aborted because 1 source files failed",
            failed_results=(
                ImportResult(
                    0,
                    "broken.CSV",
                    "ARTICLES",
                    0,
                    0,
                    status="failed",
                    error_message="ValueError: bad header",
                ),
            ),
        )

    monkeypatch.setattr(cli, "rebuild_database", fake_rebuild_database)

    exit_code = cli.main(
        ["rebuild", "--source", str(tmp_path), "--db", str(tmp_path / "db.sqlite")]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "error: Database rebuild aborted" in output
    assert "error: broken.CSV: ValueError: bad header" in output
