"""
Project Management Agents — PMBOK-style phases plus requirements, ERD, architecture, and sprint plans.

Display name: **Project Management Agents** (ids use prefix ``pm_``).
"""

from __future__ import annotations

# (id, short label, category, subfolder under --out-dir)
PROJECT_MANAGEMENT_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    ("pm_phase_initiation", "Initiation: charter, stakeholders, business case", "pmbok_initiation", "phases/01_initiation"),
    ("pm_phase_planning", "Planning: scope, schedule framework, risks, comms plan", "pmbok_planning", "phases/02_planning"),
    ("pm_phase_execution", "Execution: ways of working, quality, build coordination", "pmbok_execution", "phases/03_execution"),
    (
        "pm_phase_monitoring",
        "Monitoring & controlling: KPIs, milestones, change, RAID, status reporting",
        "pmbok_monitoring",
        "phases/04_monitoring_controlling",
    ),
    ("pm_phase_closure", "Closure: handover, lessons learned, sign-off, archive", "pmbok_closure", "phases/05_closure"),
    (
        "pm_requirements_backlog",
        "Requirements: user stories, acceptance criteria, NFRs, traceability outline",
        "artefacts",
        "artifacts/requirements",
    ),
    (
        "pm_erd_data_model",
        "Data model: conceptual + ERD (Mermaid) + key integrity rules",
        "artefacts",
        "artifacts/data_model",
    ),
    (
        "pm_backend_architecture",
        "Backend architecture: services, APIs, jobs, auth, deployment view (Mermaid where useful)",
        "artefacts",
        "artifacts/backend",
    ),
    (
        "pm_frontend_architecture",
        "Frontend architecture: app structure, routing, state, components, build vs buy",
        "artefacts",
        "artifacts/frontend",
    ),
    (
        "pm_sprint_parallel_roadmap",
        "Sprints: multi-sprint plan with parallel tracks, dependencies, deliverables per sprint",
        "artefacts",
        "artifacts/sprints",
    ),
)

PROJECT_MANAGEMENT_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in PROJECT_MANAGEMENT_AGENTS)

AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in PROJECT_MANAGEMENT_AGENTS}

DISPLAY_NAME = "Project Management Agents"


def list_pm_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat, _ in PROJECT_MANAGEMENT_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
