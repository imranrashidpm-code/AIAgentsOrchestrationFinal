"""**Localization (i18n/l10n)** — ``i18n_l10n_spec``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    LOCALIZATION_AGENTS,
    LOCALIZATION_AGENT_IDS,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "LOCALIZATION_AGENTS",
    "LOCALIZATION_AGENT_IDS",
    "run_localization_agent",
]


def __getattr__(name: str):
    if name == "run_localization_agent":
        from .factory import run_localization_agent

        return run_localization_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
