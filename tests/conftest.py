"""Shared pytest setup."""

from cm_dashboard._compat import patch_python314_typing_for_pydantic

patch_python314_typing_for_pydantic()
