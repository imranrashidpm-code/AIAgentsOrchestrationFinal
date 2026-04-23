"""Crew: Reporting Agent with read-only access to an external database."""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from agent_capabilities import enrich_agent_config, get_pack_tools

from .tools.reporting_db_tools import build_reporting_tools


@CrewBase
class ReportingCrew:
    """Single-agent crew for natural-language business reporting over external data."""

    agents_config = "config/reporting_agents.yaml"
    tasks_config = "config/reporting_tasks.yaml"

    @agent
    def reporting_agent(self) -> Agent:
        db_tools = build_reporting_tools() or []
        cap_tools = get_pack_tools("reporting") or []
        tools = [*db_tools, *cap_tools]
        return Agent(
            config=enrich_agent_config(self.agents_config["reporting_agent"]),  # type: ignore[index]
            tools=tools if tools else None,
            verbose=True,
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config["reporting_task"],  # type: ignore[index]
            agent=self.reporting_agent(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            name="reporting_agent",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
