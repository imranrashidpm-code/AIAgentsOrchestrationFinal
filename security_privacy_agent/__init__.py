"""**Security & privacy** — ``sec_privacy_threat_pii`` (advisory; not legal advice)."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    SECURITY_PRIVACY_AGENTS,
    SECURITY_PRIVACY_AGENT_IDS,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "SECURITY_PRIVACY_AGENTS",
    "SECURITY_PRIVACY_AGENT_IDS",
    "run_security_privacy_agent",
]


def __getattr__(name: str):
    if name == "run_security_privacy_agent":
        from .factory import run_security_privacy_agent

        return run_security_privacy_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
