"""**Release & distribution** — ``rel_app_distribution``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    RELEASE_DISTRIBUTION_AGENTS,
    RELEASE_DISTRIBUTION_AGENT_IDS,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "RELEASE_DISTRIBUTION_AGENTS",
    "RELEASE_DISTRIBUTION_AGENT_IDS",
    "run_release_distribution_agent",
]


def __getattr__(name: str):
    if name == "run_release_distribution_agent":
        from .factory import run_release_distribution_agent

        return run_release_distribution_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
