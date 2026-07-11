"""Command line entry points for local imports and validation."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from cm_dashboard.config import load_settings
from cm_dashboard.db import connect_database, create_database
from cm_dashboard.importing.pipeline import (
    DatabaseRebuildRequiredError,
    import_source_folder,
    rebuild_database,
)
from cm_dashboard.importing.source_scan import scan_source_files
from cm_dashboard.importing.validation import validate_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cm-dashboard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect-source")
    inspect_parser.add_argument("--source", type=Path, default=None)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--source", type=Path, default=None)
    import_parser.add_argument("--db", type=Path, default=None)

    rebuild_parser = subparsers.add_parser("rebuild")
    rebuild_parser.add_argument("--source", type=Path, default=None)
    rebuild_parser.add_argument("--db", type=Path, default=None)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--db", type=Path, default=None)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect-source":
        settings = load_settings(source_path=args.source)
        report = scan_source_files(settings.source_path)
        counts = Counter(file.metadata.file_extension.value for file in report.files)
        print(f"source: {report.source_path}")
        print(f"valid files: {len(report.files)}")
        print(f"unknown files: {len(report.unknown_files)}")
        for extension, count in sorted(counts.items()):
            print(f"{extension}: {count}")
        for unknown in report.unknown_files:
            print(f"warning: {unknown.path.name}: {unknown.issue.message}")
        return 0

    if args.command == "import":
        settings = load_settings(source_path=args.source, database_path=args.db)
        connection = create_database(settings.database_path)
        try:
            results = import_source_folder(connection, settings.source_path)
        except DatabaseRebuildRequiredError as exc:
            print(f"error: {exc}")
            return 2
        finally:
            connection.close()
        counts = Counter(result.status for result in results)
        print(f"imported files: {counts['imported']}")
        print(f"skipped files: {counts['skipped']}")
        print(f"failed files: {counts['failed']}")
        print(f"database: {settings.database_path}")
        for result in results:
            if result.status == "failed":
                print(f"error: {result.file_name}: {result.error_message}")
        return 1 if counts["failed"] else 0

    if args.command == "rebuild":
        settings = load_settings(source_path=args.source, database_path=args.db)
        results = rebuild_database(settings.source_path, settings.database_path)
        print(f"rebuilt files: {len(results)}")
        print(f"database: {settings.database_path}")
        return 0

    if args.command == "validate":
        settings = load_settings(database_path=args.db)
        connection = connect_database(settings.database_path)
        try:
            issues = validate_database(connection)
        finally:
            connection.close()
        print(f"issues: {len(issues)}")
        for issue in issues:
            print(f"{issue.severity}: {issue.code}: {issue.message}")
        return 0

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
