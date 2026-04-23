"""
Design Agents — UX/UI, IA, wireframes, visual design, system, a11y, handoff.

User-facing name: **Design Agents** (ids use prefix ``dg_``).
"""

from __future__ import annotations

# (id, short label, category, subfolder under --out-dir)
DESIGN_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    ("dg_design_brief", "Design brief from goals & constraints", "strategy", "design/strategy"),
    ("dg_user_research", "User research & problem framing plan", "research", "design/research"),
    ("dg_information_architecture", "IA, navigation & content structure", "ux", "design/ux"),
    ("dg_wireframe_spec", "Wireframes & key interaction flows (low-fi spec)", "ux", "design/ux"),
    ("dg_visual_ui", "Visual design: layout, look & feel, components from the prompt", "ui", "design/ui"),
    (
        "dg_design_system",
        "Design tokens, components & patterns (starter design system)",
        "systems",
        "design/system",
    ),
    ("dg_accessibility_spec", "Accessibility acceptance criteria & checklist (WCAG-oriented)", "quality", "design/quality"),
    ("dg_dev_handoff", "Specs for dev: assets list, redlines, edge cases, states", "handoff", "design/handoff"),
)

DESIGN_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in DESIGN_AGENTS)

# Relative path (POSIX-style) for documentation layout
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in DESIGN_AGENTS}

DISPLAY_NAME = "Design Agents"


def list_design_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat, _ in DESIGN_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
