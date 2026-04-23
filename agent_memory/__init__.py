"""
Persistent, per-**agent_id** run memory: prior prompts and output excerpts are re-injected on the
next run so the model can stay consistent. This is **not** model fine-tuning; it is retrieval of
your past runs from disk.
"""

from .store import (
    augment_context,
    is_memory_enabled,
    merge_inputs_with_memory,
    merge_reporting_inputs_with_memory,
    merge_sdlc_inputs_with_memory,
    record_run,
    reset_agent_memory,
)

__all__ = [
    "augment_context",
    "is_memory_enabled",
    "merge_inputs_with_memory",
    "merge_reporting_inputs_with_memory",
    "merge_sdlc_inputs_with_memory",
    "record_run",
    "reset_agent_memory",
]
