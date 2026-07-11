"""FastAPI application shell."""
# ruff: noqa: E402

from __future__ import annotations

import csv
import inspect
import io
import sqlite3
import typing
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode


def _patch_python314_typing_for_pydantic() -> None:
    original_eval_type = getattr(typing, "_eval_type", None)
    if original_eval_type is None or getattr(original_eval_type, "_cm_dashboard_patched", False):
        return
    if "prefer_fwd_module" in inspect.signature(original_eval_type).parameters:
        return

    def patched_eval_type(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        kwargs.pop("prefer_fwd_module", None)
        return original_eval_type(*args, **kwargs)

    patched_eval_type.__dict__["_cm_dashboard_patched"] = True
    typing.__dict__["_eval_type"] = patched_eval_type


_patch_python314_typing_for_pydantic()

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware

from cm_dashboard.config import load_settings
from cm_dashboard.db import connect_database, create_database
from cm_dashboard.importing.pipeline import database_requires_rebuild
from cm_dashboard.reporting.queries import (
    DEFAULT_DATE_BASIS,
    AmbiguousShipmentError,
    ReportingFilters,
    count_article_lines,
    count_shipments,
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
PAGE_SIZE = 100
IMPORT_STATUSES = {"pending", "processing", "imported", "failed", "conflict"}
STATIC_VERSION = max(
    path.stat().st_mtime_ns for path in (WEB_DIR / "static").iterdir() if path.is_file()
)
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
templates.env.filters["direction_label"] = lambda value: {
    "PURCHASED": "Gekauft",
    "SOLD": "Verkauft",
}.get(value, value)
templates.env.filters["date_basis_label"] = lambda value: {
    "PAYMENTDATE": "Zahlungsdatum",
    "PURCHASEDATE": "Kaufdatum",
}.get(value, value)
templates.env.filters["entity_label"] = lambda value: {
    "ARTICLES": "Artikel",
    "SHIPMENTS": "Sendungen",
}.get(value, value)
templates.env.filters["status_label"] = lambda value: {
    "pending": "Ausstehend",
    "processing": "In Verarbeitung",
    "imported": "Importiert",
    "failed": "Fehlgeschlagen",
    "conflict": "Konflikt",
}.get(value, value)
templates.env.filters["severity_label"] = lambda value: {
    "info": "Info",
    "warning": "Warnung",
    "error": "Fehler",
}.get(value, value)
templates.env.globals["static_version"] = STATIC_VERSION


@dataclass(frozen=True)
class Pagination:
    page: int
    page_size: int
    total_count: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def page_count(self) -> int:
        return max(1, (self.total_count + self.page_size - 1) // self.page_size)

    @property
    def first_item(self) -> int:
        return self.offset + 1 if self.offset < self.total_count else 0

    @property
    def last_item(self) -> int:
        return min(self.offset + self.page_size, self.total_count)


def create_app(database_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(
        title="Cardmarket History Dashboard",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.database_path = load_settings(database_path=database_path).database_path
    initial_connection = create_database(app.state.database_path)
    initial_connection.close()
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["127.0.0.1", "localhost", "[::1]", "testserver"],
    )
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; object-src 'none'; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        )
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        else:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> Response:
        filters = _filters_from_request(request)
        with _database_connection(app.state.database_path) as connection:
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
    def imports(request: Request) -> Response:
        file_page = _validated_positive_int(
            "file_page", request.query_params.get("file_page"), default=1
        )
        issue_page = _validated_positive_int(
            "issue_page", request.query_params.get("issue_page"), default=1
        )
        with _database_connection(app.state.database_path) as connection:
            file_count = int(connection.execute("SELECT COUNT(*) FROM import_files").fetchone()[0])
            file_pagination = Pagination(file_page, PAGE_SIZE, file_count)
            files = connection.execute(
                """
                SELECT import_file_id, file_name, direction, entity, date_basis,
                       period_start, period_end, row_count, import_status
                FROM import_files
                ORDER BY import_file_id DESC
                LIMIT ? OFFSET ?
                """,
                (file_pagination.page_size, file_pagination.offset),
            ).fetchall()
            issue_count = int(
                connection.execute("SELECT COUNT(*) FROM import_issues").fetchone()[0]
            )
            issue_pagination = Pagination(issue_page, PAGE_SIZE, issue_count)
            issues = connection.execute(
                """
                SELECT import_issues.severity, import_issues.code, import_issues.message,
                       import_issues.source_row_number, import_files.file_name
                FROM import_issues
                LEFT JOIN import_files
                    ON import_files.import_file_id = import_issues.import_file_id
                ORDER BY import_issues.import_issue_id DESC
                LIMIT ? OFFSET ?
                """,
                (issue_pagination.page_size, issue_pagination.offset),
            ).fetchall()
        file_previous_url, file_next_url = _pagination_urls(
            request, file_pagination, parameter="file_page"
        )
        issue_previous_url, issue_next_url = _pagination_urls(
            request, issue_pagination, parameter="issue_page"
        )
        return templates.TemplateResponse(
            request,
            "imports.html",
            {
                "page_title": "Importe",
                "active_nav": "imports",
                "files": files,
                "issues": issues,
                "file_pagination": file_pagination,
                "file_previous_url": file_previous_url,
                "file_next_url": file_next_url,
                "issue_pagination": issue_pagination,
                "issue_previous_url": issue_previous_url,
                "issue_next_url": issue_next_url,
            },
        )

    @app.get("/shipments", response_class=HTMLResponse)
    def shipments(request: Request) -> Response:
        filters = _filters_from_request(request)
        page = _validated_positive_int("page", request.query_params.get("page"), default=1)
        with _database_connection(app.state.database_path) as connection:
            total_count = count_shipments(connection, filters)
            pagination = Pagination(page=page, page_size=PAGE_SIZE, total_count=total_count)
            rows = fetch_shipments(
                connection,
                filters,
                limit=pagination.page_size,
                offset=pagination.offset,
            )
        return templates.TemplateResponse(
            request,
            "shipments.html",
            {
                "page_title": "Sendungen",
                "active_nav": "shipments",
                "filters": filters,
                "shipments": rows,
                **_pagination_context(request, pagination),
            },
        )

    @app.get("/articles", response_class=HTMLResponse)
    def articles(request: Request) -> Response:
        filters = _filters_from_request(request)
        page = _validated_positive_int("page", request.query_params.get("page"), default=1)
        with _database_connection(app.state.database_path) as connection:
            total_count = count_article_lines(connection, filters)
            pagination = Pagination(page=page, page_size=PAGE_SIZE, total_count=total_count)
            rows = fetch_article_lines(
                connection,
                filters,
                limit=pagination.page_size,
                offset=pagination.offset,
            )
        return templates.TemplateResponse(
            request,
            "articles.html",
            {
                "page_title": "Artikelpositionen",
                "active_nav": "articles",
                "filters": filters,
                "articles": rows,
                **_pagination_context(request, pagination),
            },
        )

    @app.get("/products/{product_id}", response_class=HTMLResponse)
    def product_detail(request: Request, product_id: str) -> Response:
        page = _validated_positive_int("page", request.query_params.get("page"), default=1)
        with _database_connection(app.state.database_path) as connection:
            product = connection.execute(
                "SELECT product_id FROM products WHERE product_id = ?",
                (product_id,),
            ).fetchone()
            if product is None:
                raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
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
            total_count = count_article_lines(connection, filters)
            pagination = Pagination(page=page, page_size=PAGE_SIZE, total_count=total_count)
            articles = fetch_article_lines(
                connection,
                filters,
                limit=pagination.page_size,
                offset=pagination.offset,
            )
            totals = period_totals(connection, filters)
        return templates.TemplateResponse(
            request,
            "product_detail.html",
            {
                "page_title": f"Produkt {product_id}",
                "active_nav": "articles",
                "product": product,
                "labels": labels,
                "articles": articles,
                "totals": totals,
                **_pagination_context(request, pagination),
            },
        )

    @app.get("/reports/period.csv")
    def period_report(request: Request) -> Response:
        filters = _filters_from_request(request)
        with _database_connection(app.state.database_path) as connection:
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
    ) -> Response:
        validated_direction = _validated_choice(
            "direction", direction, {"PURCHASED", "SOLD"}
        )
        validated_date_basis = _validated_choice(
            "date_basis",
            date_basis,
            {"PURCHASEDATE", "PAYMENTDATE"},
            default=DEFAULT_DATE_BASIS,
        )
        assert validated_date_basis is not None
        with _database_connection(app.state.database_path) as connection:
            try:
                shipment = fetch_shipment_detail(
                    connection, order_id, direction=validated_direction
                )
            except AmbiguousShipmentError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            if shipment is None:
                raise HTTPException(status_code=404, detail="Sendung nicht gefunden")
            events = fetch_shipment_events(connection, shipment["shipment_id"])
            articles = fetch_shipment_articles(
                connection,
                shipment["shipment_id"],
                date_basis=validated_date_basis,
            )
        return templates.TemplateResponse(
            request,
            "shipment_detail.html",
            {
                "page_title": f"Sendung {order_id}",
                "active_nav": "shipments",
                "shipment": shipment,
                "events": events,
                "articles": articles,
                "date_basis": validated_date_basis,
            },
        )

    return app


app = create_app()


@contextmanager
def _database_connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    connection = connect_database(database_path)
    try:
        if database_requires_rebuild(connection):
            raise HTTPException(
                status_code=503,
                detail=(
                    "Die Datenbanknormalisierung ist veraltet; "
                    "bitte den Befehl rebuild ausfuehren"
                ),
            )
        yield connection
    finally:
        connection.close()


def _filters_from_request(request: Request) -> ReportingFilters:
    start_date = _validated_date("start_date", request.query_params.get("start_date"))
    end_date = _validated_date("end_date", request.query_params.get("end_date"))
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=422, detail="Das Bis-Datum darf nicht vor dem Von-Datum liegen"
        )
    min_amount = _validated_decimal("min_amount", request.query_params.get("min_amount"))
    max_amount = _validated_decimal("max_amount", request.query_params.get("max_amount"))
    min_quantity = _validated_nonnegative_int(
        "min_quantity", request.query_params.get("min_quantity")
    )
    max_quantity = _validated_nonnegative_int(
        "max_quantity", request.query_params.get("max_quantity")
    )
    _validate_range("amount", min_amount, max_amount)
    _validate_range("quantity", min_quantity, max_quantity)
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
        order_id=_query_text(request, "order_id"),
        product_id=_query_text(request, "product_id"),
        product_text=_query_text(request, "product_text"),
        expansion=_query_text(request, "expansion"),
        category=_query_text(request, "category"),
        username=_query_text(request, "username"),
        counterparty_name=_query_text(request, "counterparty_name"),
        country=_query_text(request, "country"),
        currency=(_query_text(request, "currency") or "").upper() or None,
        min_amount=min_amount,
        max_amount=max_amount,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        comments=_query_text(request, "comments"),
        import_file=_query_text(request, "import_file"),
        import_status=_validated_choice(
            "import_status",
            _query_text(request, "import_status"),
            IMPORT_STATUSES,
        ),
        link_status=_validated_choice(
            "link_status",
            _query_text(request, "link_status"),
            {"linked", "unlinked"},
        ),
    )


def _validated_date(name: str, value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail=f"{name} muss ein ISO-Datum sein"
        ) from exc


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
        raise HTTPException(
            status_code=422, detail=f"{name} muss einer dieser Werte sein: {choices}"
        )
    return normalized


def _validated_positive_int(name: str, value: str | None, *, default: int) -> int:
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail=f"{name} muss eine positive Ganzzahl sein"
        ) from exc
    if parsed <= 0:
        raise HTTPException(status_code=422, detail=f"{name} muss eine positive Ganzzahl sein")
    return parsed


def _validated_nonnegative_int(name: str, value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail=f"{name} muss eine nicht negative Ganzzahl sein"
        ) from exc
    if parsed < 0:
        raise HTTPException(
            status_code=422, detail=f"{name} muss eine nicht negative Ganzzahl sein"
        )
    return parsed


def _validated_decimal(name: str, value: str | None) -> float | None:
    if not value:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise HTTPException(
            status_code=422, detail=f"{name} muss eine Dezimalzahl sein"
        ) from exc
    if not parsed.is_finite():
        raise HTTPException(status_code=422, detail=f"{name} muss eine endliche Dezimalzahl sein")
    return float(parsed)


def _validate_range(
    name: str,
    minimum: int | float | None,
    maximum: int | float | None,
) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=422, detail=f"min_{name} darf max_{name} nicht ueberschreiten"
        )


def _query_text(request: Request, name: str) -> str | None:
    value = request.query_params.get(name)
    return value.strip() or None if value else None


def _pagination_context(
    request: Request, pagination: Pagination
) -> dict[str, object | None]:
    previous_url, next_url = _pagination_urls(request, pagination, parameter="page")
    return {
        "pagination": pagination,
        "previous_url": previous_url,
        "next_url": next_url,
    }


def _pagination_urls(
    request: Request, pagination: Pagination, *, parameter: str
) -> tuple[str | None, str | None]:
    previous_url = (
        _page_url(request, pagination.page - 1, parameter=parameter)
        if pagination.page > 1
        else None
    )
    next_url = (
        _page_url(request, pagination.page + 1, parameter=parameter)
        if pagination.page < pagination.page_count
        else None
    )
    return previous_url, next_url


def _page_url(request: Request, page: int, *, parameter: str) -> str:
    query = [(key, value) for key, value in request.query_params.items() if key != parameter]
    if page > 1:
        query.append((parameter, str(page)))
    encoded = urlencode(query)
    return f"{request.url.path}?{encoded}" if encoded else request.url.path


def _mask_text(value: object | None) -> str:
    text = "" if value is None else str(value)
    if len(text) <= 1:
        return "*" if text else ""
    if len(text) == 2:
        return f"{text[0]}*"
    return f"{text[0]}***{text[-1]}"


def _csv_body(rows: list[dict[str, typing.Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=PERIOD_REPORT_FIELDS,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
