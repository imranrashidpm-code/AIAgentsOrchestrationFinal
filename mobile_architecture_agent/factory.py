from __future__ import annotations

from typing import Any

from crewai import Agent, Crew, Process, Task

from agent_capabilities import enrich_agent_config, get_pack_tools, prepare_standard_agent_inputs, record_run

from .config_loader import load_mob_agents, load_mob_tasks
from .registry import MOBILE_ARCHITECTURE_AGENT_IDS

_PACK = "mobile_architecture_agent"

_ag: dict | None = None
_tk: dict | None = None


def _agents() -> dict:
    global _ag
    if _ag is None:
        _ag = load_mob_agents()
    return _ag


def _tasks() -> dict:
    global _tk
    if _tk is None:
        _tk = load_mob_tasks()
    return _tk


def run_mobile_architecture_agent(agent_id: str, inputs: dict[str, str]) -> Any:
    if agent_id not in MOBILE_ARCHITECTURE_AGENT_IDS:
        raise ValueError(
            f"Unknown mobile architecture agent_id '{agent_id}'. Valid: {sorted(MOBILE_ARCHITECTURE_AGENT_IDS)}",
        )
    ac, tc = _agents(), _tasks()
    if agent_id not in ac:
        raise KeyError(f"Agent YAML missing: {agent_id}")
    task_key = f"{agent_id}_task"
    if task_key not in tc:
        raise KeyError(f"Task YAML missing: {task_key}")
    up = (inputs.get("user_prompt") or "").strip() or (
        "Describe a greenfield mobile architecture for a B2B field-service app on iOS and Android."
    )
    merged, effective = prepare_standard_agent_inputs(
        _PACK,
        agent_id,
        user_prompt=up,
        constraints=inputs.get("constraints") or "None specified.",
        business_context=inputs.get("business_context") or "None specified.",
    )
    tool_list = get_pack_tools(_PACK)
    agent = Agent(
        config=enrich_agent_config(ac[agent_id]),  # type: ignore[arg-type]
        tools=tool_list if tool_list else None,
        verbose=True,
    )
    task = Task(config=tc[task_key], agent=agent)  # type: ignore[arg-type]
    crew = Crew(name=agent_id, agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff(inputs=merged)
    record_run(agent_id, effective, result)
    return result
