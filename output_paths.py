"""Write agent markdown to a subfolder (used by design and project-management CLIs)."""

from __future__ import annotations

import re
from pathlib import Path

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_\-]+")


def sanitize_filename(stem: str) -> str:
    s = _SAFE_NAME.sub("_", (stem or "output").strip())[:200]
    return s or "output"


def write_agent_markdown(
    base_dir: Path,
    *relative_parts: str,
    filename: str,
    body: str,
) -> Path:
    """
    Create parent dirs and write UTF-8 markdown. Returns the path written.
    """
    sub = base_dir.joinpath(*relative_parts)
    sub.mkdir(parents=True, exist_ok=True)
    path = sub / filename
    text = body if str(body).endswith("\n") else str(body) + "\n"
    path.write_text(text, encoding="utf-8")
    return path
