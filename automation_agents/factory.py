"""Build a one-agent, one-task Crew for any registered automation agent id."""

from __future__ import annotations

from typing import Any

from crewai import Agent, Crew, Process, Task

from agent_capabilities import (
    enrich_agent_config,
    get_pack_tools,
    prepare_standard_agent_inputs,
    record_run,
)

from .config_loader import load_merged_agents, load_merged_tasks
from .registry import AUTOMATION_AGENT_IDS

_PACK = "automation"

_agents_cache: dict | None = None
_tasks_cache: dict | None = None


def _agents() -> dict:
    global _agents_cache
    if _agents_cache is None:
        _agents_cache = load_merged_agents()
    return _agents_cache


def _tasks() -> dict:
    global _tasks_cache
    if _tasks_cache is None:
        _tasks_cache = load_merged_tasks()
    return _tasks_cache


def run_automation_agent(agent_id: str, inputs: dict[str, str]) -> Any:
    """
    Run a single automation agent by id. ``inputs`` may include:

    - ``user_prompt`` (optional but recommended)
    - ``constraints`` (optional)
    - ``business_context`` (optional) — paste ERP data, policy text, or log excerpts
    """
    if agent_id not in AUTOMATION_AGENT_IDS:
        raise ValueError(
            f"Unknown agent_id '{agent_id}'. Valid ids: {sorted(AUTOMATION_AGENT_IDS)}",
        )
    agents_cfg = _agents()
    tasks_cfg = _tasks()
    if agent_id not in agents_cfg:
        raise KeyError(f"Agent config missing in YAML: {agent_id}")
    task_key = f"{agent_id}_task"
    if task_key not in tasks_cfg:
        raise KeyError(f"Task config missing in YAML: {task_key}")

    up = (inputs.get("user_prompt") or "").strip()
    if not up:
        up = (
            "No detailed prompt was provided. Apply your role to produce a useful template output "
            "the business can fill in (checklist, table structure, or questions to clarify)."
        )

    merged_inputs, effective = prepare_standard_agent_inputs(
        _PACK,
        agent_id,
        user_prompt=up,
        constraints=inputs.get("constraints") or "None specified.",
        business_context=inputs.get("business_context") or "None specified.",
    )

    tool_list = get_pack_tools(_PACK)
    agent = Agent(
        config=enrich_agent_config(agents_cfg[agent_id]),  # type: ignore[arg-type]
        tools=tool_list if tool_list else None,
        verbose=True,
    )
    task = Task(
        config=tasks_cfg[task_key],  # type: ignore[arg-type]
        agent=agent,
    )
    crew = Crew(
        name=agent_id,
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff(inputs=merged_inputs)
    record_run(agent_id, effective, result)
    return result
