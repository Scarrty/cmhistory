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


WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def create_app() -> FastAPI:
    app = FastAPI(title="Cardmarket History Dashboard")
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

    return app


app = create_app()
