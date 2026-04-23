"""**API & contract** — ``api_openapi_contract``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    API_CONTRACT_AGENTS,
    API_CONTRACT_AGENT_IDS,
    DISPLAY_NAME,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "API_CONTRACT_AGENTS",
    "API_CONTRACT_AGENT_IDS",
    "DISPLAY_NAME",
    "run_api_contract_agent",
]


def __getattr__(name: str):
    if name == "run_api_contract_agent":
        from .factory import run_api_contract_agent

        return run_api_contract_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
