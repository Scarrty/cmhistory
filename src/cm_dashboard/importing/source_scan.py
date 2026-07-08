"""Source folder scanning for Cardmarket exports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from cm_dashboard.importing.filename import (
    FilenameParseIssue,
    ParsedFilename,
    parse_filename,
)


IMPORTABLE_EXTENSIONS = {".xls", ".xlsx", ".csv"}


@dataclass(frozen=True)
class SourceFile:
    path: Path
    metadata: ParsedFilename


@dataclass(frozen=True)
class UnknownSourceFile:
    path: Path
    issue: FilenameParseIssue


@dataclass(frozen=True)
class SourceScanReport:
    source_path: Path
    files: tuple[SourceFile, ...]
    unknown_files: tuple[UnknownSourceFile, ...]

    @property
    def total_candidates(self) -> int:
        return len(self.files) + len(self.unknown_files)

    @property
    def extension_counts(self) -> dict[str, int]:
        return dict(Counter(file.metadata.file_extension.value for file in self.files))


def scan_source_files(source_path: str | Path) -> SourceScanReport:
    root = Path(source_path).expanduser().resolve(strict=False)
    if not root.is_dir():
        issue = FilenameParseIssue(file_name=root.name, message=f"Source path is not a directory: {root}")
        return SourceScanReport(
            source_path=root,
            files=(),
            unknown_files=(UnknownSourceFile(path=root, issue=issue),),
        )

    files: list[SourceFile] = []
    unknown_files: list[UnknownSourceFile] = []
    for candidate in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        if not candidate.is_file() or candidate.suffix.lower() not in IMPORTABLE_EXTENSIONS:
            continue

        result = parse_filename(candidate)
        if result.metadata is not None:
            files.append(SourceFile(path=candidate.resolve(strict=False), metadata=result.metadata))
        elif result.issue is not None:
            unknown_files.append(
                UnknownSourceFile(path=candidate.resolve(strict=False), issue=result.issue)
            )

    return SourceScanReport(
        source_path=root,
        files=tuple(files),
        unknown_files=tuple(unknown_files),
    )
