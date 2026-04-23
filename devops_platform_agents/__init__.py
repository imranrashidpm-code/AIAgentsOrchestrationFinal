"""**DevOps & platform** — ``dvp_*`` agents. CLI: ``devops_platform_run.py``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DEVOPS_PLATFORM_AGENTS,
    DEVOPS_PLATFORM_AGENT_IDS,
    DISPLAY_NAME,
    list_by_category,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DEVOPS_PLATFORM_AGENTS",
    "DEVOPS_PLATFORM_AGENT_IDS",
    "DISPLAY_NAME",
    "list_by_category",
    "run_devops_platform_agent",
]


def __getattr__(name: str):
    if name == "run_devops_platform_agent":
        from .factory import run_devops_platform_agent

        return run_devops_platform_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
