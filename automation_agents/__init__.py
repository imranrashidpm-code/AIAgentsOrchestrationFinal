"""
Automation Agents — individual ERP/operations agents, each invocable on its own.

Run via CLI: ``python automation_run.py <agent_id> --prompt "..."``
Or API: ``POST /v1/automation/{agent_id}``
"""

from .registry import (
    AUTOMATION_AGENT_IDS,
    AUTOMATION_AGENTS,
    list_agents_by_category,
)

__all__ = [
    "AUTOMATION_AGENT_IDS",
    "AUTOMATION_AGENTS",
    "list_agents_by_category",
    "run_automation_agent",
]


def __getattr__(name: str):
    if name == "run_automation_agent":
        from .factory import run_automation_agent

        return run_automation_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
