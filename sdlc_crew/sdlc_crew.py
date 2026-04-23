"""Professional SDLC crew: gathering -> analysis -> architecture -> database ->
web -> Android -> iOS -> desktop -> QA -> DevOps. Tasks run sequentially; each
stage receives prior task outputs via context. Parallel module runs use parallel_runner."""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from agent_capabilities import enrich_agent_config, get_pack_tools


@CrewBase
class SdlcCrew:
    """Ten-agent crew: separate specialists per client platform after database design."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def _sdlc_agent(self, yaml_key: str) -> Agent:
        t = get_pack_tools("sdlc")
        return Agent(
            config=enrich_agent_config(self.agents_config[yaml_key]),  # type: ignore[index]
            tools=t if t else None,
            verbose=True,
        )

    @agent
    def requirements_gatherer(self) -> Agent:
        return self._sdlc_agent("requirements_gatherer")

    @agent
    def business_analyst(self) -> Agent:
        return self._sdlc_agent("business_analyst")

    @agent
    def system_architect(self) -> Agent:
        return self._sdlc_agent("system_architect")

    @agent
    def database_engineer(self) -> Agent:
        return self._sdlc_agent("database_engineer")

    @agent
    def web_application_engineer(self) -> Agent:
        return self._sdlc_agent("web_application_engineer")

    @agent
    def android_application_engineer(self) -> Agent:
        return self._sdlc_agent("android_application_engineer")

    @agent
    def ios_application_engineer(self) -> Agent:
        return self._sdlc_agent("ios_application_engineer")

    @agent
    def desktop_application_engineer(self) -> Agent:
        return self._sdlc_agent("desktop_application_engineer")

    @agent
    def qa_engineer(self) -> Agent:
        return self._sdlc_agent("qa_engineer")

    @agent
    def devops_engineer(self) -> Agent:
        return self._sdlc_agent("devops_engineer")

    @task
    def requirements_gathering_task(self) -> Task:
        return Task(
            config=self.tasks_config["requirements_gathering_task"],  # type: ignore[index]
            agent=self.requirements_gatherer(),
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],  # type: ignore[index]
            agent=self.business_analyst(),
            context=[self.requirements_gathering_task()],
        )

    @task
    def architecture_task(self) -> Task:
        return Task(
            config=self.tasks_config["architecture_task"],  # type: ignore[index]
            agent=self.system_architect(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
            ],
        )

    @task
    def database_development_task(self) -> Task:
        return Task(
            config=self.tasks_config["database_development_task"],  # type: ignore[index]
            agent=self.database_engineer(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
                self.architecture_task(),
            ],
        )

    @task
    def web_application_task(self) -> Task:
        return Task(
            config=self.tasks_config["web_application_task"],  # type: ignore[index]
            agent=self.web_application_engineer(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
                self.architecture_task(),
                self.database_development_task(),
            ],
        )

    @task
    def android_application_task(self) -> Task:
        return Task(
            config=self.tasks_config["android_application_task"],  # type: ignore[index]
            agent=self.android_application_engineer(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
                self.architecture_task(),
                self.database_development_task(),
                self.web_application_task(),
            ],
        )

    @task
    def ios_application_task(self) -> Task:
        return Task(
            config=self.tasks_config["ios_application_task"],  # type: ignore[index]
            agent=self.ios_application_engineer(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
                self.architecture_task(),
                self.database_development_task(),
                self.web_application_task(),
                self.android_application_task(),
            ],
        )

    @task
    def desktop_application_task(self) -> Task:
        return Task(
            config=self.tasks_config["desktop_application_task"],  # type: ignore[index]
            agent=self.desktop_application_engineer(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
                self.architecture_task(),
                self.database_development_task(),
                self.web_application_task(),
                self.android_application_task(),
                self.ios_application_task(),
            ],
        )

    @task
    def qa_task(self) -> Task:
        return Task(
            config=self.tasks_config["qa_task"],  # type: ignore[index]
            agent=self.qa_engineer(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
                self.architecture_task(),
                self.database_development_task(),
                self.web_application_task(),
                self.android_application_task(),
                self.ios_application_task(),
                self.desktop_application_task(),
            ],
        )

    @task
    def devops_task(self) -> Task:
        return Task(
            config=self.tasks_config["devops_task"],  # type: ignore[index]
            agent=self.devops_engineer(),
            context=[
                self.requirements_gathering_task(),
                self.analysis_task(),
                self.architecture_task(),
                self.database_development_task(),
                self.web_application_task(),
                self.android_application_task(),
                self.ios_application_task(),
                self.desktop_application_task(),
                self.qa_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            name="sdlc_full_pipeline",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
