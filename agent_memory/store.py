"""
JSONL on-disk store: one file per ``agent_id`` under ``AGENT_MEMORY_DIR`` (default ``.agent_memory``).

Environment:
  ``AGENT_MEMORY`` — ``1``/``true`` (default on) to enable; ``0``/``false`` to disable.
  ``AGENT_MEMORY_DIR`` — override base directory.
  ``AGENT_MEMORY_MAX_OUTPUT_CHARS`` — cap stored output (default 12000).
  ``AGENT_MEMORY_LAST_N`` — how many prior runs to inject (default 6).
  ``AGENT_MEMORY_MAX_INJECT_CHARS`` — max size of the injected block (default 10000).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")

_DEFAULT_DIR = Path(".agent_memory")


def is_memory_enabled() -> bool:
    v = (os.environ.get("AGENT_MEMORY", "1") or "1").strip().lower()
    return v in ("1", "true", "yes", "on")


def _memory_dir() -> Path:
    p = (os.environ.get("AGENT_MEMORY_DIR") or "").strip()
    return Path(p) if p else _DEFAULT_DIR


def _safe_agent_id(agent_id: str) -> str:
    s = _SAFE.sub("_", (agent_id or "unknown").strip())[:200]
    return s or "unknown"


def _jsonl_path(agent_id: str) -> Path:
    return _memory_dir() / f"{_safe_agent_id(agent_id)}.jsonl"


def _max_out() -> int:
    try:
        return max(1_000, int(os.environ.get("AGENT_MEMORY_MAX_OUTPUT_CHARS", "12000")))
    except ValueError:
        return 12_000


def _last_n() -> int:
    try:
        return max(1, min(50, int(os.environ.get("AGENT_MEMORY_LAST_N", "6"))))
    except ValueError:
        return 6


def _max_inject() -> int:
    try:
        return max(2_000, int(os.environ.get("AGENT_MEMORY_MAX_INJECT_CHARS", "10000")))
    except ValueError:
        return 10_000


def _tail_lines(path: Path, n: int) -> list[str]:
    if not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    return lines[-n:] if len(lines) > n else lines


def _format_prior_block(agent_id: str) -> str:
    path = _jsonl_path(agent_id)
    lines = _tail_lines(path, _last_n())
    if not lines:
        return ""
    parts: list[str] = []
    for ln in lines:
        try:
            o = json.loads(ln)
        except json.JSONDecodeError:
            continue
        ts = o.get("ts", "?")
        up = (o.get("user_prompt") or o.get("user_report_prompt") or o.get("project_brief") or "")[
            :1_200
        ]
        op = (o.get("output_excerpt") or "")[:1_200]
        parts.append(
            f"- **{ts}** — Request (excerpt): {up}\n  · Prior output (excerpt): {op}\n"
        )
    text = "\n".join(parts)
    cap = _max_inject()
    if len(text) > cap:
        text = text[: cap - 20] + "\n… [memory truncated]\n"
    return text


def augment_context(
    agent_id: str,
    current_body: str,
    *,
    section_label: str = "User / business context (this run)",
) -> str:
    """
    Prepend retrieved prior runs to a single context field (e.g. ``business_context``,
    ``reporting_context``, or ``project_brief``). If memory is off or there is no history, returns
    ``current_body`` unchanged.
    """
    if not is_memory_enabled():
        return current_body
    block = _format_prior_block(agent_id)
    if not block:
        return current_body
    return (
        "## Prior work memory (same agent / pipeline id: continuity)\n"
        "Use this to stay aligned with how you / the team have been working. "
        "Do not repeat large chunks verbatim; refine and build on it.\n\n"
        f"{block}\n\n## {section_label}\n{current_body}"
    )


def record_run(
    agent_id: str,
    effective_inputs: dict[str, str],
    raw_result: Any,
) -> None:
    """
    Append one run: ``effective_inputs`` should be the **user-facing** fields (not the augmented
    context). ``raw_result`` is typically a CrewOutput with ``.raw`` text.
    """
    if not is_memory_enabled():
        return
    out = getattr(raw_result, "raw", None) or str(raw_result) or ""
    out = str(out)[:_max_out()]
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "user_prompt": (effective_inputs.get("user_prompt") or "")[:8_000],
        "constraints": (effective_inputs.get("constraints") or "")[:4_000],
        "business_context": (effective_inputs.get("business_context") or "")[:8_000],
        "user_report_prompt": (effective_inputs.get("user_report_prompt") or "")[:8_000],
        "reporting_context": (effective_inputs.get("reporting_context") or "")[:4_000],
        "project_brief": (effective_inputs.get("project_brief") or "")[:8_000],
        "module_scope": (effective_inputs.get("module_scope") or "")[:2_000],
        "sprint_context": (effective_inputs.get("sprint_context") or "")[:2_000],
        "output_excerpt": out,
    }
    path = _jsonl_path(agent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def merge_sdlc_inputs_with_memory(
    agent_id: str,
    inputs: dict[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    """SDLC crew: memory is prepended to ``project_brief``."""
    pb = (inputs.get("project_brief") or "").strip() or "None specified."
    cons = inputs.get("constraints") or "None specified."
    ms = inputs.get("module_scope") or "Full product"
    sc = inputs.get("sprint_context") or "Full pipeline"
    effective = {
        "project_brief": inputs.get("project_brief") or "",
        "constraints": cons,
        "module_scope": ms,
        "sprint_context": sc,
    }
    if not is_memory_enabled():
        kick = {
            "project_brief": inputs.get("project_brief") or pb,
            "constraints": cons,
            "module_scope": ms,
            "sprint_context": sc,
        }
        return kick, effective
    merged = {
        "project_brief": augment_context(agent_id, pb, section_label="Project brief (this run)"),
        "constraints": cons,
        "module_scope": ms,
        "sprint_context": sc,
    }
    return merged, effective


def merge_reporting_inputs_with_memory(
    agent_id: str,
    user_report_prompt: str,
    reporting_context: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """Reporting crew: memory is prepended to ``reporting_context``."""
    urp = user_report_prompt
    rc = reporting_context or "None specified."
    effective = {"user_report_prompt": urp, "reporting_context": rc}
    if not is_memory_enabled():
        return effective.copy(), effective
    merged = {
        "user_report_prompt": urp,
        "reporting_context": augment_context(
            agent_id,
            rc,
            section_label="Reporting context (this run)",
        ),
    }
    return merged, effective


def merge_inputs_with_memory(
    agent_id: str,
    *,
    user_prompt: str,
    constraints: str,
    business_context: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Build kickoff inputs with memory merged into ``business_context``.
    Returns ``(merged_for_kickoff, effective_for_record)`` where effective has the **user** business
    context only (no memory block), for accurate storage.
    """
    cons = constraints or "None specified."
    user_bc = business_context or "None specified."
    effective = {
        "user_prompt": user_prompt,
        "constraints": cons,
        "business_context": user_bc,
    }
    if not is_memory_enabled():
        return effective.copy(), effective
    merged = {
        "user_prompt": user_prompt,
        "constraints": cons,
        "business_context": augment_context(agent_id, user_bc),
    }
    return merged, effective


def reset_agent_memory(agent_id: str) -> bool:
    """Delete stored memory for one agent id. Returns True if a file was removed."""
    p = _jsonl_path(agent_id)
    if p.is_file():
        p.unlink()
        return True
    return False
