"""Integration & BFF — edge composition, third-party APIs, outbox, anti-corruption layer."""

from __future__ import annotations

INTEGRATION_BFF_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "int_bff_patterns",
        "Integration & BFF: edge composition, partner APIs, events, failure modes",
        "integration",
        "platform/integration",
    ),
)

INTEGRATION_BFF_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in INTEGRATION_BFF_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in INTEGRATION_BFF_AGENTS}
DISPLAY_NAME = "Integration & BFF"
