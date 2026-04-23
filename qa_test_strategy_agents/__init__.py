"""**QA & test strategy** — ``qts_*`` agents. CLI: ``qa_test_strategy_run.py``."""

from .registry import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    QA_TEST_STRATEGY_AGENTS,
    QA_TEST_STRATEGY_AGENT_IDS,
    list_by_category,
)

__all__ = [
    "AGENT_OUTPUT_SUBDIR",
    "DISPLAY_NAME",
    "QA_TEST_STRATEGY_AGENTS",
    "QA_TEST_STRATEGY_AGENT_IDS",
    "list_by_category",
    "run_qa_test_strategy_agent",
]


def __getattr__(name: str):
    if name == "run_qa_test_strategy_agent":
        from .factory import run_qa_test_strategy_agent

        return run_qa_test_strategy_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
