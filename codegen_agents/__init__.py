"""**Codegen** — generate a project tree from spec markdown, ZIP from ``codegen_agents/Output/``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    CODEGEN_AGENTS,
    CODEGEN_AGENT_IDS,
    DISPLAY_NAME,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "CODEGEN_AGENTS",
    "CODEGEN_AGENT_IDS",
    "DISPLAY_NAME",
    "run_codegen_from_spec",
]


def __getattr__(name: str):
    if name == "run_codegen_from_spec":
        from .pipeline import run_codegen_from_spec

        return run_codegen_from_spec
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
