"""SQLite connection and migration helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

MIGRATIONS_PATH = Path(__file__).resolve().parent / "migrations"


def connect_database(database_path: str | Path) -> sqlite3.Connection:
    path = str(database_path)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def create_database(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    if str(database_path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect_database(database_path)
    apply_migrations(connection)
    return connection


def apply_migrations(
    connection: sqlite3.Connection,
    *,
    migrations_path: str | Path = MIGRATIONS_PATH,
) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    applied = {
        row["migration_id"]
        for row in connection.execute("SELECT migration_id FROM schema_migrations").fetchall()
    }

    for migration in _migration_files(Path(migrations_path)):
        migration_id = migration.name
        if migration_id in applied:
            continue
        with connection:
            connection.executescript(migration.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO schema_migrations (migration_id) VALUES (?)",
                (migration_id,),
            )


def _migration_files(migrations_path: Path) -> Iterable[Path]:
    return sorted(migrations_path.glob("*.sql"), key=lambda path: path.name)
