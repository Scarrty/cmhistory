from pathlib import Path

from cm_dashboard.config import (
    DATABASE_PATH_ENV,
    SOURCE_PATH_ENV,
    load_settings,
    normalize_path,
)


def test_default_settings_use_working_directory_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(SOURCE_PATH_ENV, raising=False)
    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    settings = load_settings()

    assert settings.source_path == tmp_path.resolve(strict=False)
    assert settings.database_path == (tmp_path / "data" / "cardmarket.db").resolve(strict=False)


def test_environment_variables_override_default_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(SOURCE_PATH_ENV, str(tmp_path / "exports"))
    monkeypatch.setenv(DATABASE_PATH_ENV, str(tmp_path / "db" / "cardmarket.db"))

    settings = load_settings()

    assert settings.source_path == (tmp_path / "exports").resolve(strict=False)
    assert settings.database_path == (tmp_path / "db" / "cardmarket.db").resolve(strict=False)


def test_explicit_paths_take_precedence_over_environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(DATABASE_PATH_ENV, str(tmp_path / "ignored.db"))

    settings = load_settings(database_path=tmp_path / "explicit.db")

    assert settings.database_path == (tmp_path / "explicit.db").resolve(strict=False)


def test_explicit_absolute_paths_are_preserved(tmp_path: Path) -> None:
    source_path = tmp_path / "source"
    database_path = tmp_path / "db" / "cardmarket.db"

    settings = load_settings(source_path=source_path, database_path=database_path)

    assert settings.source_path == source_path.resolve(strict=False)
    assert settings.database_path == database_path.resolve(strict=False)


def test_relative_paths_are_normalized_from_current_working_directory(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    settings = load_settings(source_path="exports", database_path="data/test.db")

    assert settings.source_path == (tmp_path / "exports").resolve(strict=False)
    assert settings.database_path == (tmp_path / "data" / "test.db").resolve(strict=False)


def test_normalize_path_can_use_explicit_base_path(tmp_path: Path) -> None:
    base_path = tmp_path / "base"

    assert normalize_path("nested/file.db", base_path=base_path) == (
        base_path / "nested" / "file.db"
    ).resolve(strict=False)
