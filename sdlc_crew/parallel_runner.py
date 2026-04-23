"""Run one or more SDLC pipeline executions in parallel (e.g. per module / sprint)."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from agent_capabilities import prepare_sdlc_inputs, record_run

from .sdlc_crew import SdlcCrew

_SDLC_MEM_ID = "sdlc_full_pipeline"


def _merge_job_inputs(
    base_brief: str,
    base_constraints: str,
    job: dict[str, Any],
) -> dict[str, str]:
    return {
        "project_brief": str(job.get("project_brief") or base_brief),
        "constraints": str(job.get("constraints") or base_constraints),
        "module_scope": str(job.get("module_scope") or "Full product"),
        "sprint_context": str(job.get("sprint_context") or "Full pipeline"),
    }


def run_single_pipeline(inputs: dict[str, str]) -> Any:
    """Execute one sequential crew with the given kickoff inputs."""
    merged, eff = prepare_sdlc_inputs("sdlc", _SDLC_MEM_ID, inputs)
    result = SdlcCrew().crew().kickoff(inputs=merged)
    record_run(_SDLC_MEM_ID, eff, result)
    return result


def run_parallel_pipelines(
    jobs: list[dict[str, Any]],
    base_brief: str,
    base_constraints: str,
    *,
    max_workers: int = 4,
) -> list[tuple[dict[str, str], Any]]:
    """
    Run multiple independent SDLC pipelines concurrently (e.g. different modules).

    Each job dict may include: project_brief, constraints, module_scope, sprint_context.
    Omitted fields fall back to base_brief / base_constraints / defaults.
    Returns (merged_inputs, crew_result) pairs in the same order as ``jobs``.
    """
    merged = [_merge_job_inputs(base_brief, base_constraints, j) for j in jobs]
    results: list[tuple[dict[str, str], Any]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(run_single_pipeline, inp) for inp in merged]
        for inp, fut in zip(merged, futures):
            results.append((inp, fut.result()))

    return results


def load_parallel_jobs_from_json(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON array of job objects from a file."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Parallel jobs file must be a JSON array of objects.")
    return [dict(x) for x in data]
