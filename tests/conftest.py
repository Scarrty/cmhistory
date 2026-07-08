"""Shared pytest setup."""

from cm_dashboard.web.app import _patch_python314_typing_for_pydantic

_patch_python314_typing_for_pydantic()
