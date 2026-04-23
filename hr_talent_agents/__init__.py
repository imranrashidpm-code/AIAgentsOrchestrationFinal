"""**HR & talent** — ``hrt_*`` agents. Drafts only; not legal advice. CLI: ``hr_talent_run.py``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    HR_TALENT_AGENTS,
    HR_TALENT_AGENT_IDS,
    list_by_category,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "HR_TALENT_AGENTS",
    "HR_TALENT_AGENT_IDS",
    "list_by_category",
    "run_hr_talent_agent",
]


def __getattr__(name: str):
    if name == "run_hr_talent_agent":
        from .factory import run_hr_talent_agent

        return run_hr_talent_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
