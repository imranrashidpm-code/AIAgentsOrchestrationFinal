"""**Mobile architecture** — ``mob_stack_architecture``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    MOBILE_ARCHITECTURE_AGENTS,
    MOBILE_ARCHITECTURE_AGENT_IDS,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "MOBILE_ARCHITECTURE_AGENTS",
    "MOBILE_ARCHITECTURE_AGENT_IDS",
    "run_mobile_architecture_agent",
]


def __getattr__(name: str):
    if name == "run_mobile_architecture_agent":
        from .factory import run_mobile_architecture_agent

        return run_mobile_architecture_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
