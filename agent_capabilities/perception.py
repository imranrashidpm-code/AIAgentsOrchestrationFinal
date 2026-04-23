"""
Perception (input handling): normalize and bound user-provided text before reasoning.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _cap(s: str, max_len: int) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 20] + "\n… [truncated by perception layer]\n"


def is_perception_enabled() -> bool:
    v = (os.environ.get("ORCHESTRATOR_PERCEPTION", "1") or "1").strip().lower()
    return v in ("1", "true", "yes", "on")


def _max_user_prompt() -> int:
    try:
        return max(2_000, int(os.environ.get("ORCHESTRATOR_MAX_USER_PROMPT_CHARS", "48000")))
    except ValueError:
        return 48_000


def _max_other() -> int:
    try:
        return max(1_000, int(os.environ.get("ORCHESTRATOR_MAX_CONTEXT_CHARS", "96000")))
    except ValueError:
        return 96_000


def normalize_text_field(name: str, value: str | None, *, cap: int) -> str:
    if value is None:
        return ""
    t = unicodedata.normalize("NFKC", str(value))
    t = _CTRL.sub("", t)
    return _cap(t, cap)


def normalize_standard_inputs(inputs: dict[str, str]) -> dict[str, str]:
    """
    Fields: ``user_prompt``, ``constraints``, ``business_context``.
    If perception is disabled, returns a copy with string values only.
    """
    base = {k: str(v) if v is not None else "" for k, v in inputs.items()}
    if not is_perception_enabled():
        return base
    return {
        "user_prompt": normalize_text_field("user_prompt", base.get("user_prompt"), cap=_max_user_prompt()),
        "constraints": normalize_text_field("constraints", base.get("constraints"), cap=_max_other()),
        "business_context": normalize_text_field("business_context", base.get("business_context"), cap=_max_other()),
    }


def perception_preamble() -> str:
    """Short line inserted into context when perception runs (for auditability)."""
    if not is_perception_enabled():
        return ""
    return (
        "[Perception] Inputs were normalized (Unicode NFKC, control chars removed, length caps applied). "
        f"Max prompt ≈ {_max_user_prompt()} chars, max other fields ≈ {_max_other()} chars.\n\n"
    )


def normalize_sdlc_inputs(inputs: dict[str, str]) -> dict[str, str]:
    """Perception for SDLC kickoff fields."""
    base = {k: str(v) if v is not None else "" for k, v in inputs.items()}
    if not is_perception_enabled():
        return base
    return {
        "project_brief": normalize_text_field("project_brief", base.get("project_brief"), cap=_max_user_prompt()),
        "constraints": normalize_text_field("constraints", base.get("constraints"), cap=_max_other()),
        "module_scope": _cap(_CTRL.sub("", unicodedata.normalize("NFKC", base.get("module_scope", ""))), 8_000),
        "sprint_context": _cap(_CTRL.sub("", unicodedata.normalize("NFKC", base.get("sprint_context", ""))), 8_000),
    }


def normalize_reporting_inputs(inputs: dict[str, str]) -> dict[str, str]:
    """Perception for reporting kickoff."""
    base = {k: str(v) if v is not None else "" for k, v in inputs.items()}
    if not is_perception_enabled():
        return base
    urp = base.get("user_report_prompt") or base.get("user_prompt") or ""
    ctx = base.get("reporting_context") or ""
    return {
        "user_report_prompt": normalize_text_field("user_report_prompt", urp, cap=_max_user_prompt()),
        "reporting_context": normalize_text_field("reporting_context", ctx, cap=_max_other()),
    }
