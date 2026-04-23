"""
Flattened catalog of every runnable agent for the **orchestrated** (auto-planned) mode.

Includes two special rows that are not Crew YAML agents: ``sdlc_sequential`` and ``business_report``.
"""

from __future__ import annotations

SPECIAL_ORCHESTRATED: tuple[tuple[str, str, str, str], ...] = (
    (
        "sdlc_crew",
        "sdlc_sequential",
        "SDLC documentation pipeline (multi-agent, sequential)",
        "sdlc",
    ),
    (
        "reporting",
        "business_report",
        "Business / SQL reporting from natural language (Reporting agent)",
        "reporting",
    ),
)


def get_flat_catalog() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(pack: str, agent_id: str, label: str, category: str) -> None:
        rows.append(
            {
                "pack": pack,
                "agent_id": agent_id,
                "label": (label or "")[:500],
                "category": (category or "")[:200],
            }
        )

    from automation_agents.registry import AUTOMATION_AGENTS

    for a in AUTOMATION_AGENTS:
        add("automation_agents", a[0], a[1], a[2])

    from data_analytics_agents.registry import DATA_ANALYTICS_AGENTS

    for a in DATA_ANALYTICS_AGENTS:
        add("data_analytics_agents", a[0], a[1], a[2])

    from design_agents.registry import DESIGN_AGENTS

    for a in DESIGN_AGENTS:
        add("design_agents", a[0], a[1], a[2])

    from devops_platform_agents.registry import DEVOPS_PLATFORM_AGENTS

    for a in DEVOPS_PLATFORM_AGENTS:
        add("devops_platform_agents", a[0], a[1], a[2])

    from hr_talent_agents.registry import HR_TALENT_AGENTS

    for a in HR_TALENT_AGENTS:
        add("hr_talent_agents", a[0], a[1], a[2])

    from project_management_agents.registry import PROJECT_MANAGEMENT_AGENTS

    for a in PROJECT_MANAGEMENT_AGENTS:
        add("project_management_agents", a[0], a[1], a[2])

    from qa_test_strategy_agents.registry import QA_TEST_STRATEGY_AGENTS

    for a in QA_TEST_STRATEGY_AGENTS:
        add("qa_test_strategy_agents", a[0], a[1], a[2])

    from sales_marketing_agents.registry import SALES_MARKETING_AGENTS

    for a in SALES_MARKETING_AGENTS:
        add("sales_marketing_agents", a[0], a[1], a[2])

    from api_contract_agent.registry import API_CONTRACT_AGENTS

    for a in API_CONTRACT_AGENTS:
        add("api_contract_agent", a[0], a[1], a[2])

    from integration_bff_agent.registry import INTEGRATION_BFF_AGENTS

    for a in INTEGRATION_BFF_AGENTS:
        add("integration_bff_agent", a[0], a[1], a[2])

    from localization_agent.registry import LOCALIZATION_AGENTS

    for a in LOCALIZATION_AGENTS:
        add("localization_agent", a[0], a[1], a[2])

    from mobile_architecture_agent.registry import MOBILE_ARCHITECTURE_AGENTS

    for a in MOBILE_ARCHITECTURE_AGENTS:
        add("mobile_architecture_agent", a[0], a[1], a[2])

    from observability_agent.registry import OBSERVABILITY_AGENTS

    for a in OBSERVABILITY_AGENTS:
        add("observability_agent", a[0], a[1], a[2])

    from release_distribution_agent.registry import RELEASE_DISTRIBUTION_AGENTS

    for a in RELEASE_DISTRIBUTION_AGENTS:
        add("release_distribution_agent", a[0], a[1], a[2])

    from security_privacy_agent.registry import SECURITY_PRIVACY_AGENTS

    for a in SECURITY_PRIVACY_AGENTS:
        add("security_privacy_agent", a[0], a[1], a[2])

    for a in SPECIAL_ORCHESTRATED:
        add(a[0], a[1], a[2], a[3])

    return rows


def catalog_key_set() -> frozenset[tuple[str, str]]:
    return frozenset((r["pack"], r["agent_id"]) for r in get_flat_catalog())


def catalog_lines_for_prompt(max_lines: int = 500) -> str:
    lines: list[str] = []
    for r in get_flat_catalog()[:max_lines]:
        lines.append(f"{r['pack']}\t{r['agent_id']}\t{r['label']}\t{r['category']}")
    return "\n".join(lines)
