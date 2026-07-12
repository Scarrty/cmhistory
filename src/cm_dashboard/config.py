"""Application path configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

SOURCE_PATH_ENV = "CM_DASHBOARD_SOURCE"
DATABASE_PATH_ENV = "CM_DASHBOARD_DB"


def normalize_path(path: str | Path, *, base_path: Path | None = None) -> Path:
    """Return an absolute path without requiring it to exist."""

    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (base_path or Path.cwd()) / candidate
    return candidate.resolve(strict=False)


def default_source_path() -> Path:
    """Default source folder: CM_DASHBOARD_SOURCE or the working directory."""

    configured = os.environ.get(SOURCE_PATH_ENV)
    if configured:
        return normalize_path(configured)
    return Path.cwd().resolve(strict=False)


def default_database_path() -> Path:
    """Default database file: CM_DASHBOARD_DB or data/cardmarket.db in the working directory."""

    configured = os.environ.get(DATABASE_PATH_ENV)
    if configured:
        return normalize_path(configured)
    return (Path.cwd() / "data" / "cardmarket.db").resolve(strict=False)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for local import and dashboard commands."""

    source_path: Path
    database_path: Path


def load_settings(
    *,
    source_path: str | Path | None = None,
    database_path: str | Path | None = None,
) -> Settings:
    return Settings(
        source_path=normalize_path(source_path)
        if source_path is not None
        else default_source_path(),
        database_path=normalize_path(database_path)
        if database_path is not None
        else default_database_path(),
    )
