"""
LLM planner: chooses an ordered list of (pack, agent_id) steps for a user goal.
"""

from __future__ import annotations

import json
import os
from typing import Any

from agent_capabilities.brain import resolve_llm

from .catalog import catalog_key_set, catalog_lines_for_prompt


def _max_steps() -> int:
    try:
        return max(3, min(16, int(os.environ.get("ORCHESTRATED_MAX_STEPS", "10"))))
    except ValueError:
        return 10


def plan_workflow(
    *,
    user_prompt: str,
    constraints: str,
    business_context: str,
    llm_model: str | None = None,
) -> dict[str, Any]:
    """
    Returns ``{ "rationale": str, "steps": [ { "pack", "agent_id", "user_prompt", "constraints", "business_context" } ] }``.
    """
    from openai import OpenAI

    keys = catalog_key_set()
    catalog_text = catalog_lines_for_prompt()
    ms = _max_steps()

    system = f"""You are a senior delivery architect. Given a user goal, output a JSON object with:
- "rationale": short string why this plan fits the request.
- "steps": array of {ms} or fewer steps (minimum 3 when the request is non-trivial). Each step MUST be an object with:
  - "pack": exact string from the catalog (first column)
  - "agent_id": exact string from the catalog (second column)
  - "user_prompt": focused sub-task for THAT agent only (markdown ok, be specific)
  - "constraints": string (use "None specified." if none)
  - "business_context": string (summarise prior context + this project; use "None specified." if empty)

Rules:
1. Only use (pack, agent_id) pairs that appear in the catalog. No invented ids.
2. Order steps logically: e.g. requirements/SDLC → design → mobile/api/security architecture → devops/qa → localization as needed.
3. For **comprehensive product documentation** (greenfield app, new system), often include `sdlc_crew` + `sdlc_sequential` early, OR `project_management_agents` + `pm_requirements_backlog` first.
4. For **Android/iOS/mobile** work include `mobile_architecture_agent` + `mob_stack_architecture`.
5. For **UI** include `design_agents` (`dg_wireframe_spec` and/or `dg_visual_ui` or `dg_dev_handoff`).
6. For **test strategy** include a `qa_test_strategy_agents` agent.
7. For **APIs / feeds / RSS / JSON** include `api_contract_agent` and/or `integration_bff_agent` as appropriate.
8. For **CI/release** use `devops_platform_agents` or `release_distribution_agent` when relevant.
9. Use `reporting` + `business_report` only when the user needs SQL/BI-style business reporting from the existing reporting stack — not for generic mobile app build docs.
10. Keep ERP `automation_agents` for operations/ERP flows; skip them for simple consumer/mobile apps unless the user mentions ERP.
11. Shorter projects: fewer steps; complex projects: up to {ms} steps.

Catalog (tab-separated: pack, agent_id, label, category):
{catalog_text}
"""

    user = f"""## User goal
{user_prompt}

## Constraints
{constraints}

## Business / product context
{business_context}
"""

    model = (llm_model or "").strip() or resolve_llm()
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = (resp.choices[0].message.content or "").strip()
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Planner returned non-object JSON")

    steps = data.get("steps")
    if not isinstance(steps, list):
        raise ValueError("Planner JSON missing 'steps' array")

    fixed: list[dict[str, str]] = []
    for s in steps[:ms]:
        if not isinstance(s, dict):
            continue
        p = str(s.get("pack") or "").strip()
        a = str(s.get("agent_id") or "").strip()
        if (p, a) not in keys:
            continue
        fixed.append(
            {
                "pack": p,
                "agent_id": a,
                "user_prompt": str(s.get("user_prompt") or user_prompt)[:20000],
                "constraints": str(s.get("constraints") or constraints or "None specified.")[:20000],
                "business_context": str(s.get("business_context") or business_context or "None specified.")[:20000],
            }
        )

    if len(fixed) < 2:
        raise ValueError("Planner produced no valid steps after validation")

    data["steps"] = fixed
    data["rationale"] = str(data.get("rationale") or "Planned multi-agent run.")[:5000]
    return data
