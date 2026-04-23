"""Release & app distribution — CI/CD, stores, betas, feature flags, staged rollout."""

from __future__ import annotations

RELEASE_DISTRIBUTION_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "rel_app_distribution",
        "Release: mobile/web delivery, betas, stores, feature flags, promotion pipeline",
        "release",
        "platform/release",
    ),
)

RELEASE_DISTRIBUTION_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in RELEASE_DISTRIBUTION_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in RELEASE_DISTRIBUTION_AGENTS}
DISPLAY_NAME = "Release & distribution"
