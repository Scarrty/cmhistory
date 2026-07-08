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

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cm_dashboard.config import load_settings
from cm_dashboard.db import create_database
from cm_dashboard.reporting.queries import (
    ReportingFilters,
    fetch_shipments,
    monthly_totals,
    period_totals,
)


WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
templates.env.filters["mask_text"] = lambda value: _mask_text(value)


def create_app(database_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Cardmarket History Dashboard")
    app.state.database_path = load_settings(database_path=database_path).database_path
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        filters = _filters_from_request(request)
        connection = create_database(app.state.database_path)
        totals = period_totals(connection, filters)
        monthly = monthly_totals(connection, filters)
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "page_title": "Dashboard",
                "active_nav": "dashboard",
                "filters": filters,
                "totals": totals,
                "monthly": monthly,
                "max_monthly_total": max((row["total"] for row in monthly), default=0),
            },
        )

    @app.get("/imports", response_class=HTMLResponse)
    def imports(request: Request):
        connection = create_database(app.state.database_path)
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

    @app.get("/shipments", response_class=HTMLResponse)
    def shipments(request: Request):
        filters = _filters_from_request(request)
        connection = create_database(app.state.database_path)
        rows = fetch_shipments(connection, filters)
        return templates.TemplateResponse(
            request,
            "shipments.html",
            {
                "page_title": "Shipments",
                "active_nav": "shipments",
                "filters": filters,
                "shipments": rows,
            },
        )

    @app.get("/shipments/{order_id}", response_class=HTMLResponse)
    def shipment_detail(request: Request, order_id: str):
        connection = create_database(app.state.database_path)
        shipment = connection.execute(
            "SELECT * FROM shipments WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if shipment is None:
            raise HTTPException(status_code=404, detail="Shipment not found")
        events = connection.execute(
            """
            SELECT event_type, event_datetime
            FROM shipment_events
            WHERE shipment_id = ?
            ORDER BY event_datetime
            """,
            (shipment["shipment_id"],),
        ).fetchall()
        articles = connection.execute(
            """
            SELECT article_lines.*, import_files.file_name
            FROM article_lines
            LEFT JOIN import_files
                ON import_files.import_file_id = article_lines.source_import_file_id
            WHERE article_lines.shipment_id = ?
            ORDER BY article_lines.article_line_id
            """,
            (shipment["shipment_id"],),
        ).fetchall()
        return templates.TemplateResponse(
            request,
            "shipment_detail.html",
            {
                "page_title": f"Shipment {order_id}",
                "active_nav": "shipments",
                "shipment": shipment,
                "events": events,
                "articles": articles,
            },
        )

    return app


app = create_app()


def _filters_from_request(request: Request) -> ReportingFilters:
    start_date = request.query_params.get("start_date") or None
    end_date = request.query_params.get("end_date") or None
    return ReportingFilters(
        start_date=start_date,
        end_date=end_date,
        direction=request.query_params.get("direction") or None,
        date_basis=request.query_params.get("date_basis") or None,
        order_id=request.query_params.get("order_id") or None,
        product_id=request.query_params.get("product_id") or None,
        product_text=request.query_params.get("product_text") or None,
        expansion=request.query_params.get("expansion") or None,
        category=request.query_params.get("category") or None,
        username=request.query_params.get("username") or None,
        country=request.query_params.get("country") or None,
    )


def _mask_text(value) -> str:
    text = "" if value is None else str(value)
    if len(text) <= 1:
        return "*" if text else ""
    if len(text) == 2:
        return f"{text[0]}*"
    return f"{text[0]}***{text[-1]}"
