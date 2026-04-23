"""Run SDLC documentation crew, then the Reporting agent with SDLC output as context."""

from __future__ import annotations

import os
from typing import Any

from agent_capabilities import prepare_reporting_inputs, record_run

from .parallel_runner import run_single_pipeline
from .reporting_crew import ReportingCrew

_REPORTING_MEM_ID = "reporting_agent"


def run_sdlc_then_reporting(
    sdlc_inputs: dict[str, str],
    *,
    user_report_prompt: str,
    reporting_extra: str = "",
) -> tuple[Any, Any]:
    """
    1) Execute the full SDLC sequential crew.
    2) Pass truncated SDLC text into ``reporting_context`` and run the Reporting Agent.

    Returns ``(sdlc_result, reporting_result)`` (CrewAI kickoff results).
    """
    sdlc_result = run_single_pipeline(sdlc_inputs)
    raw = getattr(sdlc_result, "raw", None) or ""
    cap = int(os.environ.get("REPORTING_SDLC_CONTEXT_MAX", "120000"))
    snippet = raw[:cap]
    if len(raw) > cap:
        snippet += "\n\n[... SDLC output truncated; increase REPORTING_SDLC_CONTEXT_MAX if needed ...]"

    parts: list[str] = [
        "## SDLC pipeline output (background for reporting)\n\n" + snippet,
    ]
    extra = (reporting_extra or "").strip()
    if extra and extra != "None specified.":
        parts.append("## Additional reporting context from user\n\n" + extra)

    final_reporting_ctx = "\n\n".join(parts)
    rep_merged, rep_eff = prepare_reporting_inputs(
        "reporting",
        _REPORTING_MEM_ID,
        user_report_prompt,
        final_reporting_ctx,
    )
    reporting_result = ReportingCrew().crew().kickoff(inputs=rep_merged)
    record_run(_REPORTING_MEM_ID, rep_eff, reporting_result)
    return sdlc_result, reporting_result
