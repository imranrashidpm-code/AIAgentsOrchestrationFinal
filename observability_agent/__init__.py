"""**Observability** — ``obs_product_platform``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    OBSERVABILITY_AGENTS,
    OBSERVABILITY_AGENT_IDS,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "OBSERVABILITY_AGENTS",
    "OBSERVABILITY_AGENT_IDS",
    "run_observability_agent",
]


def __getattr__(name: str):
    if name == "run_observability_agent":
        from .factory import run_observability_agent

        return run_observability_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
