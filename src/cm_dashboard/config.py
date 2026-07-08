"""Application path configuration."""

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_PATH = PROJECT_ROOT
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "cardmarket.db"


def normalize_path(path: str | Path, *, base_path: Path | None = None) -> Path:
    """Return an absolute path without requiring it to exist."""

    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (base_path or Path.cwd()) / candidate
    return candidate.resolve(strict=False)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for local import and dashboard commands."""

    source_path: Path = DEFAULT_SOURCE_PATH
    database_path: Path = DEFAULT_DATABASE_PATH


def load_settings(
    *,
    source_path: str | Path | None = None,
    database_path: str | Path | None = None,
) -> Settings:
    return Settings(
        source_path=normalize_path(source_path)
        if source_path is not None
        else DEFAULT_SOURCE_PATH.resolve(strict=False),
        database_path=normalize_path(database_path)
        if database_path is not None
        else DEFAULT_DATABASE_PATH.resolve(strict=False),
    )
