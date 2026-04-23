"""**Data & analytics** — ``dta_*`` agents. CLI: ``data_analytics_run.py``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DATA_ANALYTICS_AGENTS,
    DATA_ANALYTICS_AGENT_IDS,
    DISPLAY_NAME,
    list_by_category,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DATA_ANALYTICS_AGENTS",
    "DATA_ANALYTICS_AGENT_IDS",
    "DISPLAY_NAME",
    "list_by_category",
    "run_data_analytics_agent",
]


def __getattr__(name: str):
    if name == "run_data_analytics_agent":
        from .factory import run_data_analytics_agent

        return run_data_analytics_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
