"""Interpreter compatibility workarounds.

Importing this module must stay side-effect free; callers invoke the patch
functions explicitly before importing the affected third-party packages.
"""

from __future__ import annotations

import inspect
import typing


def patch_python314_typing_for_pydantic() -> None:
    """Drop the prefer_fwd_module keyword pydantic passes to typing._eval_type.

    Pydantic releases that predate the final Python 3.14 typing API call
    typing._eval_type with a prefer_fwd_module keyword the stdlib does not
    accept. The patch is a no-op on interpreters whose _eval_type already
    supports that keyword.
    """

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
