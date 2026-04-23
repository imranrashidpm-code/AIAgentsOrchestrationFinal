"""**Integration & BFF** — ``int_bff_patterns``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    INTEGRATION_BFF_AGENTS,
    INTEGRATION_BFF_AGENT_IDS,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "INTEGRATION_BFF_AGENTS",
    "INTEGRATION_BFF_AGENT_IDS",
    "run_integration_bff_agent",
]


def __getattr__(name: str):
    if name == "run_integration_bff_agent":
        from .factory import run_integration_bff_agent

        return run_integration_bff_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
