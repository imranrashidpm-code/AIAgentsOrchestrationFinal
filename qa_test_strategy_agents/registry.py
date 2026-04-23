"""
QA & test strategy — test plans, risk-based testing, E2E scope, regression strategy.

Display name: **QA & test strategy** (ids ``qts_*``).
"""

from __future__ import annotations

QA_TEST_STRATEGY_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    ("qts_test_plan", "Master test plan (scope, levels, environments, exit criteria)", "planning", "qa/planning"),
    ("qts_risk_based_testing", "Risk-based testing (RBT) matrix and prioritization", "risk", "qa/risk"),
    ("qts_e2e_feature_scope", "E2E scope for a feature (journeys, data, environments)", "e2e", "qa/e2e"),
    (
        "qts_regression_strategy",
        "Regression strategy (automation, smoke, release train alignment)",
        "regression",
        "qa/regression",
    ),
)

QA_TEST_STRATEGY_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in QA_TEST_STRATEGY_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in QA_TEST_STRATEGY_AGENTS}
DISPLAY_NAME = "QA & test strategy"


def list_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat, _ in QA_TEST_STRATEGY_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
