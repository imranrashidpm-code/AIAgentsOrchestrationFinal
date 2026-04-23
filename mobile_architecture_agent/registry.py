"""
Mobile architecture — native vs cross-platform, navigation, offline, push, auth, distribution (high level).

**One agent** per dedicated pack folder: ``mob_stack_architecture``.
"""

from __future__ import annotations

MOBILE_ARCHITECTURE_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "mob_stack_architecture",
        "Mobile system architecture (iOS/Android/cross-platform, modules, risks)",
        "mobile",
        "platform/mobile",
    ),
)

MOBILE_ARCHITECTURE_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in MOBILE_ARCHITECTURE_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in MOBILE_ARCHITECTURE_AGENTS}
DISPLAY_NAME = "Mobile architecture"
