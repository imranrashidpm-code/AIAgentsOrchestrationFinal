"""
Mandatory agent capabilities for every pack:

1. **Brain** — :func:`enrich_agent_config` (``ORCHESTRATOR_AGENT_LLM`` / ``OPENAI_MODEL_NAME``)
2. **Memory** — :mod:`agent_memory` (persistence; see ``AGENT_MEMORY``)
3. **Tools** — :func:`get_pack_tools` (stack-status tool) + pack-specific tools (e.g. SQL on Reporting)
4. **Perception** — :mod:`perception` (input normalization; ``ORCHESTRATOR_PERCEPTION``)
5. **Planning** — :mod:`planning` (goal-oriented block; ``ORCHESTRATOR_PLANNING``)
6. **Governance** — :mod:`governance` (safety; ``ORCHESTRATOR_GOVERNANCE``)

Use :func:`prepare_standard_agent_inputs`, :func:`prepare_sdlc_inputs`, or
:func:`prepare_reporting_inputs` in :mod:`pipeline` to apply perception → memory → optional layers.
"""

from .brain import (
    enrich_agent_config,
    reasoning_model_from_env,
    reset_request_llm_model,
    resolve_llm,
    set_request_llm_model,
)
from .pipeline import (
    is_capability_layers_enabled,
    prepare_reporting_inputs,
    prepare_sdlc_inputs,
    prepare_standard_agent_inputs,
)
# ``tools`` imports CrewAI — lazy-load via __getattr__ so ``api_server`` and clients can start without the full stack.

from agent_memory import (
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
    "enrich_agent_config",
    "get_pack_tools",
    "is_capability_layers_enabled",
    "is_memory_enabled",
    "merge_inputs_with_memory",
    "merge_reporting_inputs_with_memory",
    "merge_sdlc_inputs_with_memory",
    "orchestrator_tool_descriptions",
    "prepare_reporting_inputs",
    "prepare_sdlc_inputs",
    "prepare_standard_agent_inputs",
    "reasoning_model_from_env",
    "reset_request_llm_model",
    "resolve_llm",
    "set_request_llm_model",
    "record_run",
    "reset_agent_memory",
]


def __getattr__(name: str):
    if name == "get_pack_tools":
        from .tools import get_pack_tools

        return get_pack_tools
    if name == "orchestrator_tool_descriptions":
        from .tools import orchestrator_tool_descriptions

        return orchestrator_tool_descriptions
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
