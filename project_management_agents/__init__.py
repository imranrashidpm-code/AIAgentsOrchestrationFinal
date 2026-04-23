"""
Project Management Agents — initiation through closure, plus ERD, architecture, and sprint plans.

Use ``--out-dir`` on the CLI to save each run as markdown under phase/artifact folders.
"""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    PROJECT_MANAGEMENT_AGENTS,
    PROJECT_MANAGEMENT_AGENT_IDS,
    list_pm_by_category,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "PROJECT_MANAGEMENT_AGENTS",
    "PROJECT_MANAGEMENT_AGENT_IDS",
    "list_pm_by_category",
    "run_project_management_agent",
]


def __getattr__(name: str):
    if name == "run_project_management_agent":
        from .factory import run_project_management_agent

        return run_project_management_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
