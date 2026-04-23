"""**Orchestrated (auto) mode** — LLM plans which agents to run, then runs them in sequence."""

from __future__ import annotations

__all__ = [
    "get_flat_catalog",
    "orchestrated_info",
    "run_orchestrated",
]


def orchestrated_info() -> dict:
    from .catalog import get_flat_catalog

    return {
        "mode": "orchestrated",
        "description": "Single prompt; planner selects agents from the full catalog and runs them in order.",
        "catalog_size": len(get_flat_catalog()),
    }


def __getattr__(name: str):
    if name == "get_flat_catalog":
        from .catalog import get_flat_catalog

        return get_flat_catalog
    if name == "run_orchestrated":
        from .runner import run_orchestrated

        return run_orchestrated
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
