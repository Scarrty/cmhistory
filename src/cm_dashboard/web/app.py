"""FastAPI application shell."""

from __future__ import annotations

import typing
from pathlib import Path


def _patch_python314_typing_for_pydantic() -> None:
    original_eval_type = getattr(typing, "_eval_type", None)
    if original_eval_type is None or getattr(original_eval_type, "_cm_dashboard_patched", False):
        return

    def patched_eval_type(*args, **kwargs):
        kwargs.pop("prefer_fwd_module", None)
        return original_eval_type(*args, **kwargs)

    patched_eval_type._cm_dashboard_patched = True
    typing._eval_type = patched_eval_type


_patch_python314_typing_for_pydantic()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cm_dashboard.config import load_settings
from cm_dashboard.db import connect_database


WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def create_app(database_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Cardmarket History Dashboard")
    app.state.database_path = load_settings(database_path=database_path).database_path
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Dashboard",
                "active_nav": "dashboard",
            },
        )

    @app.get("/imports", response_class=HTMLResponse)
    def imports(request: Request):
        connection = connect_database(app.state.database_path)
        files = connection.execute(
            """
            SELECT import_file_id, file_name, direction, entity, date_basis,
                   period_start, period_end, row_count, import_status
            FROM import_files
            ORDER BY import_file_id DESC
            LIMIT 250
            """
        ).fetchall()
        issues = connection.execute(
            """
            SELECT import_issues.severity, import_issues.code, import_issues.message,
                   import_issues.source_row_number, import_files.file_name
            FROM import_issues
            LEFT JOIN import_files ON import_files.import_file_id = import_issues.import_file_id
            ORDER BY import_issues.import_issue_id DESC
            LIMIT 250
            """
        ).fetchall()
        return templates.TemplateResponse(
            request,
            "imports.html",
            {
                "page_title": "Imports",
                "active_nav": "imports",
                "files": files,
                "issues": issues,
            },
        )

    return app


app = create_app()
