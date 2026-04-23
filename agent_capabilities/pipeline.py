"""
Compose Perception → Memory → Governance + Planning + perception note for kickoff dicts.
"""

from __future__ import annotations

import os

from agent_memory import (
    merge_inputs_with_memory,
    merge_reporting_inputs_with_memory,
    merge_sdlc_inputs_with_memory,
)

from .governance import GOVERNANCE_BLOCK, is_governance_enabled
from .perception import is_perception_enabled, perception_preamble
from .planning import PLANNING_BLOCK, is_planning_enabled


def is_capability_layers_enabled() -> bool:
    """Master switch for governance + planning + perception notes (memory is separate)."""
    v = (os.environ.get("ORCHESTRATOR_CAPABILITIES", "1") or "1").strip().lower()
    return v in ("1", "true", "yes", "on")


def _scope_tag(agent_id: str, pack: str) -> str:
    return f"[Scope] agent_id=`{agent_id}` pack=`{pack}`."


def _prefix_layers(body: str, agent_id: str, pack: str) -> str:
    if not is_capability_layers_enabled():
        return body
    parts: list[str] = []
    if is_governance_enabled():
        parts.append(GOVERNANCE_BLOCK + "\n" + _scope_tag(agent_id, pack))
    if is_planning_enabled():
        parts.append(PLANNING_BLOCK)
    if is_perception_enabled():
        p = perception_preamble().strip()
        if p:
            parts.append(p)
    if not parts:
        return body
    return "\n\n".join(parts) + "\n\n---\n\n" + body


def prepare_standard_agent_inputs(
    pack: str,
    agent_id: str,
    *,
    user_prompt: str,
    constraints: str,
    business_context: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Perception (normalize) → memory merge → optional capability prefix on business_context.
    """
    from .perception import normalize_standard_inputs

    norm = normalize_standard_inputs(
        {
            "user_prompt": user_prompt,
            "constraints": constraints,
            "business_context": business_context,
        }
    )
    merged, eff = merge_inputs_with_memory(
        agent_id,
        user_prompt=norm["user_prompt"],
        constraints=norm["constraints"],
        business_context=norm["business_context"],
    )
    if not is_capability_layers_enabled():
        return merged, eff
    out = {**merged}
    out["business_context"] = _prefix_layers(out.get("business_context") or "None specified.", agent_id, pack)
    return out, eff


def prepare_sdlc_inputs(pack: str, agent_id: str, raw: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    from .perception import normalize_sdlc_inputs

    norm = normalize_sdlc_inputs(raw)
    merged, eff = merge_sdlc_inputs_with_memory(agent_id, norm)
    if not is_capability_layers_enabled():
        return merged, eff
    out = {**merged}
    out["project_brief"] = _prefix_layers(
        out.get("project_brief") or "None specified.",
        agent_id,
        pack,
    )
    return out, eff


def prepare_reporting_inputs(
    pack: str,
    agent_id: str,
    user_report_prompt: str,
    reporting_context: str,
) -> tuple[dict[str, str], dict[str, str]]:
    from .perception import normalize_reporting_inputs

    norm = normalize_reporting_inputs(
        {"user_report_prompt": user_report_prompt, "reporting_context": reporting_context}
    )
    merged, eff = merge_reporting_inputs_with_memory(
        agent_id,
        norm["user_report_prompt"],
        norm["reporting_context"],
    )
    if not is_capability_layers_enabled():
        return merged, eff
    out = {**merged}
    out["reporting_context"] = _prefix_layers(
        out.get("reporting_context") or "None specified.",
        agent_id,
        pack,
    )
    return out, eff
