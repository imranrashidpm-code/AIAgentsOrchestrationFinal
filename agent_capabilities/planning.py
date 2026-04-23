"""
Planning and goal-oriented behavior: inject explicit plan-then-execute instructions.
"""

from __future__ import annotations

import os

PLANNING_BLOCK = """
[Planning & goals — required approach]
1) Restate the user’s goal in one sentence.
2) List 3–7 concrete steps you will take (analysis, tables, checks, edge cases).
3) Note dependencies, assumptions, and what is out of scope.
4) Deliver the main output in structured Markdown (headings, lists, tables where useful).
5) End with open questions or validation the human should perform (if any).
""".strip()


def is_planning_enabled() -> bool:
    v = (os.environ.get("ORCHESTRATOR_PLANNING", "1") or "1").strip().lower()
    return v in ("1", "true", "yes", "on")


# Planning block is prepended in pipeline with governance & perception; see ``pipeline.py``.
