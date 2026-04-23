from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

# Text-oriented source; block obvious binaries
ALLOWED_SUFFIXES: frozenset[str] = frozenset(
    {
        ".kt",
        ".kts",
        ".java",
        ".xml",
        ".gradle",
        ".properties",
        ".md",
        ".txt",
        ".json",
        ".html",
        ".htm",
        ".css",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".cjs",
        ".mjs",
        ".m",
        ".swift",
        ".h",
        ".c",
        ".cc",
        ".cpp",
        ".hpp",
        ".py",
        ".toml",
        ".yml",
        ".yaml",
        ".sh",
        ".env",
        ".pro",
    }
)

ALLOWED_BASENAMES: frozenset[str] = frozenset(
    {
        "Dockerfile",
        "gradlew",
        "gradlew.bat",
        "Makefile",
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        "proguard-rules.pro",
    }
)


def normalize_rel_path(raw: str) -> str:
    s = (raw or "").replace("\\", "/").strip()
    return s.lstrip("/")


def is_safe_relative_path(p: str) -> bool:
    n = normalize_rel_path(p)
    if not n or len(n) > 512:
        return False
    if ".." in n or n.startswith(".."):
        return False
    if "://" in n or re.match(r"^[A-Za-z]:", n):
        return False
    parts = n.split("/")
    if len(parts) > 24:
        return False
    for part in parts:
        if not part or part in (".", "..") or re.search(r"[\x00-\x1f<>:\"|?*]", part):
            return False
    return True


def is_allowed_artifact_path(p: str) -> bool:
    n = normalize_rel_path(p)
    if not is_safe_relative_path(n):
        return False
    name = PurePosixPath(n).name
    if name in ALLOWED_BASENAMES:
        return True
    suffix = (Path(name).suffix or "").lower()
    if not suffix:
        return False
    return suffix in ALLOWED_SUFFIXES
