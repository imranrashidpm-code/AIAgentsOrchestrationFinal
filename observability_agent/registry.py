"""Observability — metrics, logs, traces, RUM/SLO alignment (product + platform)."""

from __future__ import annotations

OBSERVABILITY_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "obs_product_platform",
        "Observability: metrics, logs, traces, RUM, dashboards, SLO hooks",
        "observability",
        "platform/observability",
    ),
)

OBSERVABILITY_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in OBSERVABILITY_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in OBSERVABILITY_AGENTS}
DISPLAY_NAME = "Observability"
