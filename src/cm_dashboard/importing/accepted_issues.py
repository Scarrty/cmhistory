"""Acknowledged validation issues stored in a sidecar file next to the database.

Known, permanent coverage gaps (e.g. exports that never existed) can be
acknowledged in an ``accepted_issues.json`` file that lives next to the SQLite
database. Acknowledged gaps are excluded from the recurring validation output
and replaced by a single summary line, so new gaps stay visible. The file is
plain JSON and survives database rebuilds because it is not part of the
database itself.

File format::

    {
      "accepted_coverage": [
        "missing_period_coverage|PURCHASED|ARTICLES|PURCHASEDATE|2024-06-01|2024-06-30",
        {"fingerprint": "missing_period_coverage|...", "note": "Export existiert nicht"}
      ]
    }

Entries may be plain fingerprint strings or objects with a ``fingerprint``
key and an optional free-text ``note``.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cm_dashboard.importing.validation import ValidationIssue

ACCEPTED_ISSUES_FILENAME = "accepted_issues.json"


def coverage_fingerprint(issue: ValidationIssue) -> str | None:
    """Return the stable fingerprint of a coverage issue, or None for other codes."""

    if issue.code != "missing_period_coverage":
        return None
    if (
        issue.direction is None
        or issue.entity is None
        or issue.date_basis is None
        or issue.period_start is None
        or issue.period_end is None
    ):
        return None
    return "|".join(
        (
            issue.code,
            issue.direction,
            issue.entity,
            issue.date_basis,
            issue.period_start.isoformat(),
            issue.period_end.isoformat(),
        )
    )


def accepted_issues_path_for(connection: sqlite3.Connection) -> Path | None:
    """Locate the sidecar file next to the connection's main database file."""

    for row in connection.execute("PRAGMA database_list").fetchall():
        if row["name"] == "main":
            database_file = row["file"]
            if not database_file:
                return None
            return Path(database_file).parent / ACCEPTED_ISSUES_FILENAME
    return None


def load_accepted_fingerprints(path: Path | None) -> frozenset[str]:
    """Read acknowledged fingerprints; a missing file means nothing is accepted."""

    if path is None or not path.is_file():
        return frozenset()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    entries = payload.get("accepted_coverage", []) if isinstance(payload, dict) else None
    if entries is None or not isinstance(entries, list):
        raise ValueError(
            f"{path} must contain an object with an 'accepted_coverage' list"
        )

    fingerprints: set[str] = set()
    for entry in entries:
        fingerprint = _entry_fingerprint(entry)
        if fingerprint is None:
            raise ValueError(
                f"{path}: each accepted_coverage entry must be a fingerprint string "
                "or an object with a 'fingerprint' key"
            )
        fingerprints.add(fingerprint)
    return frozenset(fingerprints)


def accepted_fingerprints_for(connection: sqlite3.Connection) -> frozenset[str]:
    return load_accepted_fingerprints(accepted_issues_path_for(connection))


def _entry_fingerprint(entry: Any) -> str | None:
    if isinstance(entry, str) and entry:
        return entry
    if isinstance(entry, dict):
        fingerprint = entry.get("fingerprint")
        if isinstance(fingerprint, str) and fingerprint:
            return fingerprint
    return None
