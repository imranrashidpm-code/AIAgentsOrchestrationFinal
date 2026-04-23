"""
Design Agents — build UX/UI, IA, and handoff documentation from a prompt (one agent per ``dg_*`` id).

**Display name:** Design Agents. CLI: ``python design_run.py --list-agents``
"""

from .registry import AGENT_OUTPUT_SUBDIR, DESIGN_AGENTS, DESIGN_AGENT_IDS, DISPLAY_NAME, list_design_by_category

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DESIGN_AGENTS",
    "DESIGN_AGENT_IDS",
    "DISPLAY_NAME",
    "list_design_by_category",
    "run_design_agent",
]


def __getattr__(name: str):
    if name == "run_design_agent":
        from .factory import run_design_agent

        return run_design_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
