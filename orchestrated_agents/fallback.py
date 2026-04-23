"""Default multi-step plan when the LLM planner fails validation or throws."""

from __future__ import annotations


def build_fallback_plan(
    user_prompt: str,
    constraints: str,
    business_context: str,
) -> dict:
    up = (user_prompt or "").strip() or "Deliver the described product."
    cons = (constraints or "None specified.").strip() or "None specified."
    bc = (business_context or "None specified.").strip() or "None specified."
    return {
        "rationale": "Fallback sequence (requirements → design → mobile architecture → QA → API). "
        "The automatic planner failed or returned no valid steps.",
        "steps": [
            {
                "pack": "project_management_agents",
                "agent_id": "pm_requirements_backlog",
                "user_prompt": f"From this goal, produce user stories, acceptance criteria, and NFRs:\n\n{up}",
                "constraints": cons,
                "business_context": bc,
            },
            {
                "pack": "design_agents",
                "agent_id": "dg_wireframe_spec",
                "user_prompt": f"Produce low-fidelity wireframes and key flows for:\n\n{up}",
                "constraints": cons,
                "business_context": bc,
            },
            {
                "pack": "mobile_architecture_agent",
                "agent_id": "mob_stack_architecture",
                "user_prompt": f"Mobile architecture and module plan for:\n\n{up}",
                "constraints": cons,
                "business_context": bc,
            },
            {
                "pack": "api_contract_agent",
                "agent_id": "api_openapi_contract",
                "user_prompt": f"API contract outline (REST/errors/auth) for integrations implied by:\n\n{up}",
                "constraints": cons,
                "business_context": bc,
            },
            {
                "pack": "qa_test_strategy_agents",
                "agent_id": "qts_e2e_feature_scope",
                "user_prompt": f"E2E / system test scope for:\n\n{up}",
                "constraints": cons,
                "business_context": bc,
            },
        ],
    }
