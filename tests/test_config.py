from pathlib import Path

from cm_dashboard.config import DEFAULT_DATABASE_PATH, PROJECT_ROOT, load_settings, normalize_path


def test_default_settings_use_project_source_and_database_paths() -> None:
    settings = load_settings()

    assert settings.source_path == PROJECT_ROOT.resolve(strict=False)
    assert settings.database_path == DEFAULT_DATABASE_PATH.resolve(strict=False)


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
