"""
Tools (action & interaction): every agent gets a small introspection tool plus pack-specific tools
(e.g. Reporting DB tools) merged at construction time.
"""

from __future__ import annotations

import os

from crewai.tools.base_tool import BaseTool


def is_capability_tool_enabled() -> bool:
    v = (os.environ.get("ORCHESTRATOR_CAPABILITY_TOOL", "1") or "1").strip().lower()
    return v in ("1", "true", "yes", "on")


class OrchestratorStackStatusTool(BaseTool):
    """
    Return which orchestration layers are active (brain, memory, tools, perception, planning, governance).
    Use only when the user explicitly asks which capabilities or safety layers are in effect.
    """

    name: str = "orchestrator_stack_status"
    description: str = (
        "Return a short summary of which orchestration capability layers (brain/LLM env, memory, tools, "
        "perception, planning, governance) are enabled for this run. "
        "Call only if the user asks about system capabilities, guardrails, or how inputs are processed."
    )

    def _run(
        self,
        detail: str = "summary",
    ) -> str:
        caps = (os.environ.get("ORCHESTRATOR_CAPABILITIES", "1") or "1").strip()
        g = (os.environ.get("ORCHESTRATOR_GOVERNANCE", "1") or "1").strip()
        p = (os.environ.get("ORCHESTRATOR_PLANNING", "1") or "1").strip()
        pe = (os.environ.get("ORCHESTRATOR_PERCEPTION", "1") or "1").strip()
        m = (os.environ.get("AGENT_MEMORY", "1") or "1").strip()
        from agent_capabilities.brain import resolve_llm

        b = resolve_llm()
        t = (os.environ.get("ORCHESTRATOR_CAPABILITY_TOOL", "1") or "1").strip()
        return (
            f"Orchestrator layers: capabilities={caps}, governance={g}, planning={p}, perception={pe}, "
            f"agent_memory={m}, brain_model_env={b!r}, this_tool={t}.\n"
            f"(Brain uses env override when set; memory persists JSONL; governance/planning/perception "
            f"prefix context; pack-specific tools e.g. SQL are in addition to this tool.)"
        )


def get_pack_tools(pack: str) -> list[BaseTool]:
    """
    Return tools always attached to single-agent runs for the given **pack** key.
    Reporting crew adds DB tools separately in ``ReportingCrew``.
    """
    if not is_capability_tool_enabled():
        return []
    return [OrchestratorStackStatusTool()]


def orchestrator_tool_descriptions() -> str:
    return (
        f"orchestrator_stack_status: optional; when enabled (ORCHESTRATOR_CAPABILITY_TOOL) "
        f"exposes which layers are active. Pack={get_pack_tools.__name__}."
    )
