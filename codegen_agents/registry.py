"""
Codegen — generate a **text source tree** (Kotlin, XML, JS, etc.) from specification markdown, saved under ``codegen_agents/Output/``.

**Display name: Codegen from spec.**
"""

from __future__ import annotations

CODEGEN_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "codegen_from_spec",
        "Generate app/project source from markdown spec (ZIP download)",
        "codegen",
        "codegen/exports",
    ),
)

CODEGEN_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in CODEGEN_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in CODEGEN_AGENTS}
DISPLAY_NAME = "Codegen (from spec MD)"
