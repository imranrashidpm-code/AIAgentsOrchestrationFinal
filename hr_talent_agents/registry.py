"""
HR / talent — job descriptions, comp bands, interview plans, L&D, performance review structure.

Output is **draft + checklist** only — not legal advice. Display name: **HR & talent** (``hrt_*``).
"""

from __future__ import annotations

HR_TALENT_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "hrt_role_description",
        "Job description: summary, outcomes, skills, level expectations",
        "talent",
        "hr/roles",
    ),
    (
        "hrt_compensation_bands",
        "Compensation band narrative (structure, not legal advice; ranges if user provides)",
        "comp",
        "hr/compensation",
    ),
    ("hrt_interview_plan", "Structured interview plan and scorecard (bias-aware)", "hiring", "hr/hiring"),
    (
        "hrt_lnd_program_outline",
        "L&D program outline: objectives, modules, metrics",
        "learning",
        "hr/learning",
    ),
    (
        "hrt_performance_review_structure",
        "Performance / growth cycle: cadence, criteria, calibration notes, templates",
        "performance",
        "hr/performance",
    ),
)

HR_TALENT_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in HR_TALENT_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in HR_TALENT_AGENTS}
DISPLAY_NAME = "HR & talent"


def list_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat, _ in HR_TALENT_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
