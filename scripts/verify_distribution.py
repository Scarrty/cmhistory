"""Verify that built wheels contain all non-Python runtime resources."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

REQUIRED_WHEEL_FILES = {
    "cm_dashboard/migrations/001_init.sql",
    "cm_dashboard/migrations/002_import_normalization_version.sql",
    "cm_dashboard/migrations/003_directional_shipment_identity.sql",
    "cm_dashboard/migrations/004_article_lines_shipment_index.sql",
    "cm_dashboard/web/static/app.css",
    "cm_dashboard/web/static/app.js",
    "cm_dashboard/web/static/favicon.svg",
    "cm_dashboard/web/templates/base.html",
    "cm_dashboard/web/templates/dashboard.html",
}
REQUIRED_WHEEL_SUFFIXES = {
    ".dist-info/licenses/LICENSE",
    ".dist-info/licenses/NOTICE.md",
}


def verify_distribution(dist_directory: Path) -> Path:
    wheels = sorted(dist_directory.glob("cm_dashboard-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"Expected exactly one cm_dashboard wheel in {dist_directory}, found {len(wheels)}"
        )
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        archive_names = archive.namelist()
        missing = REQUIRED_WHEEL_FILES.difference(archive_names)
        missing.update(
            suffix
            for suffix in REQUIRED_WHEEL_SUFFIXES
            if not any(name.endswith(suffix) for name in archive_names)
        )
    if missing:
        formatted = ", ".join(sorted(missing))
        raise RuntimeError(f"Wheel is missing runtime resources: {formatted}")
    return wheel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    wheel = verify_distribution(args.dist)
    print(f"Verified wheel resources: {wheel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
