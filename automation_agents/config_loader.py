"""Load and merge split YAML config files for automation agents."""

from __future__ import annotations

from pathlib import Path

import yaml

_CONFIG_DIR = Path(__file__).resolve().parent / "config"


def _merge_pattern(glob: str) -> dict:
    merged: dict = {}
    for path in sorted(_CONFIG_DIR.glob(glob)):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected mapping in {path}")
        overlap = set(merged) & set(data)
        if overlap:
            raise ValueError(f"Duplicate keys when merging {path}: {sorted(overlap)}")
        merged.update(data)
    return merged


def load_merged_agents() -> dict:
    return _merge_pattern("automation_agents_*.yaml")


def load_merged_tasks() -> dict:
    return _merge_pattern("automation_tasks_*.yaml")
