"""
Dispatch a single (pack, agent_id) to the correct CrewAI runner or special pipeline.
"""

from __future__ import annotations

import os
from typing import Any


def _std_inputs(raw: dict[str, str]) -> dict[str, str]:
    return {
        "user_prompt": (raw.get("user_prompt") or "").strip() or "Complete the described task.",
        "constraints": (raw.get("constraints") or "None specified.").strip() or "None specified.",
        "business_context": (raw.get("business_context") or "None specified.").strip() or "None specified.",
    }


def execute_step(pack: str, agent_id: str, inputs: dict[str, str]) -> Any:
    """Run one agent / special pipeline. Returns CrewAI result or similar."""
    ins = _std_inputs(inputs)

    if pack == "sdlc_crew" and agent_id == "sdlc_sequential":
        from sdlc_crew.parallel_runner import run_single_pipeline

        return run_single_pipeline(
            {
                "project_brief": ins["user_prompt"],
                "constraints": ins["constraints"],
                "module_scope": "As defined in the orchestrated step",
                "sprint_context": ins["business_context"],
            }
        )

    if pack == "reporting" and agent_id == "business_report":
        from sdlc_crew import run_reporting_pipeline

        return run_reporting_pipeline(
            {
                "user_report_prompt": ins["user_prompt"],
                "reporting_context": ins["business_context"],
            }
        )

    if pack == "design_agents":
        from design_agents import run_design_agent

        r = run_design_agent(agent_id, ins)
        if agent_id == "dg_wireframe_spec":
            try:
                from design_agents.wireframe_raster import save_wireframe_dashboard_images

                text = getattr(r, "raw", None) or ""
                wm = save_wireframe_dashboard_images(
                    agent_id=agent_id,
                    user_prompt=ins["user_prompt"],
                    constraints=ins["constraints"],
                    business_context=ins["business_context"],
                    markdown_output=text,
                )
                setattr(r, "_orchestrated_wireframe_meta", wm)
            except Exception as e:
                setattr(r, "_orchestrated_wireframe_error", str(e))
        return r

    if pack == "automation_agents":
        from automation_agents import run_automation_agent

        return run_automation_agent(agent_id, ins)

    if pack == "sales_marketing_agents":
        from sales_marketing_agents import run_sales_marketing_agent

        return run_sales_marketing_agent(agent_id, ins)

    if pack == "project_management_agents":
        from project_management_agents import run_project_management_agent

        return run_project_management_agent(agent_id, ins)

    if pack == "data_analytics_agents":
        from data_analytics_agents import run_data_analytics_agent

        return run_data_analytics_agent(agent_id, ins)

    if pack == "devops_platform_agents":
        from devops_platform_agents import run_devops_platform_agent

        return run_devops_platform_agent(agent_id, ins)

    if pack == "qa_test_strategy_agents":
        from qa_test_strategy_agents import run_qa_test_strategy_agent

        return run_qa_test_strategy_agent(agent_id, ins)

    if pack == "hr_talent_agents":
        from hr_talent_agents import run_hr_talent_agent

        return run_hr_talent_agent(agent_id, ins)

    if pack == "mobile_architecture_agent":
        from mobile_architecture_agent import run_mobile_architecture_agent

        return run_mobile_architecture_agent(agent_id, ins)

    if pack == "api_contract_agent":
        from api_contract_agent import run_api_contract_agent

        return run_api_contract_agent(agent_id, ins)

    if pack == "security_privacy_agent":
        from security_privacy_agent import run_security_privacy_agent

        return run_security_privacy_agent(agent_id, ins)

    if pack == "integration_bff_agent":
        from integration_bff_agent import run_integration_bff_agent

        return run_integration_bff_agent(agent_id, ins)

    if pack == "observability_agent":
        from observability_agent import run_observability_agent

        return run_observability_agent(agent_id, ins)

    if pack == "release_distribution_agent":
        from release_distribution_agent import run_release_distribution_agent

        return run_release_distribution_agent(agent_id, ins)

    if pack == "localization_agent":
        from localization_agent import run_localization_agent

        return run_localization_agent(agent_id, ins)

    raise ValueError(f"No dispatcher for pack={pack!r} agent_id={agent_id!r}")


def result_to_text(result: Any) -> str:
    """Extract markdown/text from a crew result or string."""
    if result is None:
        return ""
    t = getattr(result, "raw", None)
    if t is not None:
        return str(t)
    return str(result)
