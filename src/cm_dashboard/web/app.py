"""FastAPI application shell."""
# ruff: noqa: E402

from __future__ import annotations

import csv
import io
import typing
from datetime import date
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
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cm_dashboard.config import load_settings
from cm_dashboard.db import create_database
from cm_dashboard.reporting.queries import (
    DEFAULT_DATE_BASIS,
    AmbiguousShipmentError,
    ReportingFilters,
    fetch_article_lines,
    fetch_shipment_articles,
    fetch_shipment_detail,
    fetch_shipment_events,
    fetch_shipments,
    monthly_totals,
    period_report_rows,
    period_totals,
)

WEB_DIR = Path(__file__).resolve().parent
PERIOD_REPORT_FIELDS = (
    "section",
    "date_basis",
    "month",
    "direction",
    "article_line_count",
    "shipment_count",
    "purchase_total",
    "sales_total",
    "total",
)
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

    @app.get("/articles", response_class=HTMLResponse)
    def articles(request: Request):
        filters = _filters_from_request(request)
        connection = create_database(app.state.database_path)
        rows = fetch_article_lines(connection, filters)
        return templates.TemplateResponse(
            request,
            "articles.html",
            {
                "page_title": "Articles",
                "active_nav": "articles",
                "filters": filters,
                "articles": rows,
            },
        )

    @app.get("/products/{product_id}", response_class=HTMLResponse)
    def product_detail(request: Request, product_id: str):
        connection = create_database(app.state.database_path)
        product = connection.execute(
            "SELECT product_id FROM products WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        filters = ReportingFilters(product_id=product_id)
        labels = connection.execute(
            """
            SELECT label
            FROM product_labels
            WHERE product_id = ?
            ORDER BY label
            """,
            (product_id,),
        ).fetchall()
        articles = fetch_article_lines(connection, filters)
        totals = period_totals(connection, filters)
        return templates.TemplateResponse(
            request,
            "product_detail.html",
            {
                "page_title": f"Product {product_id}",
                "active_nav": "articles",
                "product": product,
                "labels": labels,
                "articles": articles,
                "totals": totals,
            },
        )

    @app.get("/reports/period.csv")
    def period_report(request: Request):
        filters = _filters_from_request(request)
        connection = create_database(app.state.database_path)
        body = _csv_body(period_report_rows(connection, filters))
        return Response(
            body,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="period-report.csv"'},
        )

    @app.get("/shipments/{order_id}", response_class=HTMLResponse)
    def shipment_detail(
        request: Request,
        order_id: str,
        direction: str | None = None,
        date_basis: str = DEFAULT_DATE_BASIS,
    ):
        direction = _validated_choice("direction", direction, {"PURCHASED", "SOLD"})
        date_basis = _validated_choice(
            "date_basis",
            date_basis,
            {"PURCHASEDATE", "PAYMENTDATE"},
            default=DEFAULT_DATE_BASIS,
        )
        connection = create_database(app.state.database_path)
        try:
            shipment = fetch_shipment_detail(connection, order_id, direction=direction)
        except AmbiguousShipmentError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if shipment is None:
            raise HTTPException(status_code=404, detail="Shipment not found")
        events = fetch_shipment_events(connection, shipment["shipment_id"])
        articles = fetch_shipment_articles(
            connection,
            shipment["shipment_id"],
            date_basis=date_basis,
        )
        return templates.TemplateResponse(
            request,
            "shipment_detail.html",
            {
                "page_title": f"Shipment {order_id}",
                "active_nav": "shipments",
                "shipment": shipment,
                "events": events,
                "articles": articles,
                "date_basis": date_basis,
            },
        )

    return app


app = create_app()


def _filters_from_request(request: Request) -> ReportingFilters:
    start_date = _validated_date("start_date", request.query_params.get("start_date"))
    end_date = _validated_date("end_date", request.query_params.get("end_date"))
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must not be before start_date")
    return ReportingFilters(
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        direction=_validated_choice(
            "direction",
            request.query_params.get("direction"),
            {"PURCHASED", "SOLD"},
        ),
        date_basis=_validated_choice(
            "date_basis",
            request.query_params.get("date_basis"),
            {"PURCHASEDATE", "PAYMENTDATE"},
            default=DEFAULT_DATE_BASIS,
        ),
        order_id=request.query_params.get("order_id") or None,
        product_id=request.query_params.get("product_id") or None,
        product_text=request.query_params.get("product_text") or None,
        expansion=request.query_params.get("expansion") or None,
        category=request.query_params.get("category") or None,
        username=request.query_params.get("username") or None,
        country=request.query_params.get("country") or None,
    )


def _validated_date(name: str, value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{name} must be an ISO date") from exc


def _validated_choice(
    name: str,
    value: str | None,
    allowed: set[str],
    *,
    default: str | None = None,
) -> str | None:
    normalized = value or default
    if normalized is not None and normalized not in allowed:
        choices = ", ".join(sorted(allowed))
        raise HTTPException(status_code=422, detail=f"{name} must be one of: {choices}")
    return normalized


def _mask_text(value) -> str:
    text = "" if value is None else str(value)
    if len(text) <= 1:
        return "*" if text else ""
    if len(text) == 2:
        return f"{text[0]}*"
    return f"{text[0]}***{text[-1]}"


def _csv_body(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=PERIOD_REPORT_FIELDS,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
