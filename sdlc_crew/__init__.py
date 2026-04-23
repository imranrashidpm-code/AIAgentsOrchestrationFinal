"""CrewAI SDLC orchestration package."""

from agent_capabilities import prepare_reporting_inputs, record_run

from .full_pipeline import run_sdlc_then_reporting
from .parallel_runner import (
    load_parallel_jobs_from_json,
    run_parallel_pipelines,
    run_single_pipeline,
)
from .reporting_crew import ReportingCrew
from .sdlc_crew import SdlcCrew

_REPORTING_MEM_ID = "reporting_agent"


def run_reporting_pipeline(inputs: dict[str, str]):
    """Run the single-task Reporting crew (natural-language + optional external DB tools)."""
    urp = inputs.get("user_report_prompt") or inputs.get("user_prompt") or ""
    rctx = inputs.get("reporting_context") or "None specified."
    merged, eff = prepare_reporting_inputs("reporting", _REPORTING_MEM_ID, str(urp), str(rctx))
    result = ReportingCrew().crew().kickoff(inputs=merged)
    record_run(_REPORTING_MEM_ID, eff, result)
    return result


__all__ = [
    "ReportingCrew",
    "SdlcCrew",
    "load_parallel_jobs_from_json",
    "run_parallel_pipelines",
    "run_reporting_pipeline",
    "run_sdlc_then_reporting",
    "run_single_pipeline",
]
